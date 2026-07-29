import {existsSync, watch} from "node:fs"
import {spawn} from "node:child_process"
import path from "node:path"

const makeCommand = process.argv[2] || "make"
const converterDir = path.resolve(process.argv[3] || "proceedings-md")
const legacyConverter = process.argv[4] ? path.resolve(process.argv[4]) : undefined
const rootDir = process.cwd()

const specs = [
    {
        dir: rootDir,
        recursive: false,
        matches: name => name === "paper.md" || name === "bibliography.bib",
    },
    {
        dir: path.join(rootDir, "images"),
        recursive: true,
        matches: () => true,
    },
]

if (legacyConverter) {
    specs.push({
        dir: path.dirname(legacyConverter),
        recursive: false,
        matches: name => name === path.basename(legacyConverter),
    })
} else {
    specs.push({
        dir: converterDir,
        recursive: false,
        matches: name => name === "package.json" || name === "tsconfig.json",
    }, {
        dir: path.join(converterDir, "src"),
        recursive: true,
        matches: name => name.endsWith(".ts"),
    }, {
        dir: path.join(converterDir, "scripts"),
        recursive: false,
        matches: name => name === "build.mjs",
    }, {
        dir: path.join(converterDir, "resources"),
        recursive: false,
        matches: name => name === "isp-reference.docx",
    })
}

let rebuildTimer
let build
let rebuildPending = false

function runBuild() {
    if (build) {
        rebuildPending = true
        return
    }

    build = spawn(makeCommand, ["--no-print-directory", "build"], {
        cwd: rootDir,
        env: process.env,
        stdio: "inherit",
    })
    let settled = false
    function finishBuild(code) {
        if (settled) {
            return
        }
        settled = true
        if (code !== undefined && code !== 0) {
            console.error(`Paper rebuild failed with exit code ${code}`)
        }
        build = undefined
        if (rebuildPending) {
            rebuildPending = false
            runBuild()
        }
    }

    build.on("error", error => {
        console.error(`Failed to start ${makeCommand}: ${error.message}`)
        finishBuild(undefined)
    })
    build.on("exit", finishBuild)
}

function scheduleBuild(changedPath) {
    console.log(`Changed: ${changedPath}`)
    clearTimeout(rebuildTimer)
    rebuildTimer = setTimeout(runBuild, 100)
}

const watchers = []
for (let spec of specs) {
    if (!existsSync(spec.dir)) {
        continue
    }
    let watcher = watch(spec.dir, {recursive: spec.recursive}, (_event, filename) => {
        if (!filename) {
            return
        }
        let name = filename.toString()
        if (spec.matches(name)) {
            scheduleBuild(path.join(spec.dir, name))
        }
    })
    watcher.on("error", error => {
        console.error(`Watcher failed for ${spec.dir}: ${error.message}`)
        process.exitCode = 1
        for (let activeWatcher of watchers) {
            activeWatcher.close()
        }
    })
    watchers.push(watcher)
}

if (watchers.length === 0) {
    throw new Error("No source paths are available to watch")
}
