const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const cliProgress = require("cli-progress");

// ========================================
// INPUTS
// ========================================

const timelinePath =
  process.argv[2];

const frameDir =
  process.argv[3];

const renderedPath =
  process.argv[4];

if (!timelinePath) {

  throw new Error(
    "Missing timeline.json path"
  );
}

if (!frameDir) {

  throw new Error(
    "Missing frames directory"
  );
}

if (!renderedPath) {

  throw new Error(
    "Missing rendered.html path"
  );
}

// ========================================
// LOAD FILES
// ========================================

const timeline = JSON.parse(

  fs.readFileSync(
    timelinePath,
    "utf-8"
  )
);

const template = fs.readFileSync(

  renderedPath,
  "utf-8"
);

const segments =
  timeline.segments || [];

if (!segments.length) {

  throw new Error(
    "Timeline has no segments"
  );
}

// ========================================
// INDEXED SEGMENTS
// ========================================

const indexedSegments =

  segments.map(
    (segment, index) => ({

      ...segment,

      render_index: index
    })
  );

// ========================================
// DIRS
// ========================================

fs.mkdirSync(
  frameDir,
  { recursive: true }
);

// ========================================
// CONFIG
// ========================================

const NUM_WORKERS = 1;

// ========================================
// PROGRESS
// ========================================

const bar =
  new cliProgress.SingleBar({

    format:
      "📷 Render | {bar} | {value}/{total} | ETA: {eta_formatted}",

    barCompleteChar: "\u2588",

    barIncompleteChar: "\u2591",

    hideCursor: true

  });

let completed = 0;

// ========================================
// WORKER
// ========================================

async function renderWorker(
  tasks
) {

  const browser =
    await puppeteer.launch({

      headless: "new",

      args: [

        "--no-sandbox",

        "--disable-setuid-sandbox"
      ]
    });

  const page =
    await browser.newPage();

  await page.setViewport({

    width: 1280,

    height: 720
  });

  await page.emulateMediaFeatures([
    {
      name: "prefers-reduced-motion",
      value: "reduce"
    }
  ]);

  for (const segment of tasks) {

    try {

      const index =
        segment.line_index;

      // ==================================
      // BUILD HTML
      // ==================================

      const html =
        template.replace(

          "{{LINES}}",

          indexedSegments
            .map((s) => {

              const cls =

                s.render_index === index
                  ? "segment highlight"
                  : "segment";

              return `
                <span class="${cls}">
                  ${s.text}
                </span>
              `;
            })
            .join("\n")
        );

      // ==================================
      // SET CONTENT
      // ==================================

      await page.setContent(

        html,

        {
          waitUntil:
            "domcontentloaded"
        }
      );

      // ==================================
      // WAIT FONTS
      // ==================================

      await page.evaluate(
        () => document.fonts.ready
      );

      // ==================================
      // WAIT ELEMENT
      // ==================================

      await page.waitForSelector(
        ".segment"
      );

      // ==================================
      // SCROLL ACTIVE SEGMENT
      // ==================================

      await page.evaluate(
        (index) => {

          const elements =
            document.querySelectorAll(
              ".segment"
            );

          const el =
            elements[index];

          if (el) {

            el.scrollIntoView({

              behavior: "instant",

              block: "center"
            });
          }

        },
        index
      );

      // ==================================
      // FRAME PATH
      // ==================================

      const framePath =
        path.join(

          frameDir,

          `frame${String(index).padStart(4, "0")}.jpg`
        );

      // ==================================
      // SCREENSHOT
      // ==================================

      await page.screenshot({

        path: framePath,

        type: "jpeg",

        quality: 85
      });

      // ==================================
      // VALIDATE
      // ==================================

      if (!fs.existsSync(framePath)) {

        throw new Error(
          `Frame missing after screenshot: ${framePath}`
        );
      }

      completed++;

      bar.update(completed);

    } catch (err) {

      console.error(
        "[Renderer] ERROR:",
        err
      );

      throw err;
    }
  }

  await browser.close();
}

// ========================================
// MAIN
// ========================================

(async () => {

  const chunked =
    Array.from(
      { length: NUM_WORKERS },
      () => []
    );

  indexedSegments.forEach(
    (segment, i) => {

      chunked[
        i % NUM_WORKERS
      ].push(segment);
    }
  );

  bar.start(
    indexedSegments.length,
    0
  );

  await Promise.all(

    chunked.map(
      (tasks) =>
        renderWorker(tasks)
    )
  );

  bar.stop();

  console.log(
    "🎉 Frames rendered."
  );

})();