import { readFileSync, writeFileSync } from "fs";
import puppeteer from "puppeteer";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const inputFile = "system-diagram.mmd";
const outputFile = "system-diagram.svg";

async function renderMermaid() {
  console.log("Starting browser...");
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const page = await browser.newPage();

    // Read the mermaid diagram content
    const diagramContent = readFileSync(join(__dirname, inputFile), "utf8");

    // Create HTML with mermaid and icon packs
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { margin: 0; padding: 20px; background-color: white; }
    #diagram { display: inline-block; }
  </style>
</head>
<body>
  <div id="diagram"></div>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

    // Register icon packs
    mermaid.registerIconPacks([
      {
        name: 'logos',
        loader: () =>
          fetch('https://cdn.jsdelivr.net/npm/@iconify-json/logos@1/icons.json')
            .then(res => res.json())
      }
    ]);

    // Initialize mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default'
    });

    // Render the diagram
    const diagramContent = \`${diagramContent.replace(/`/g, "\\`")}\`;

    try {
      const { svg } = await mermaid.render('mermaid-diagram', diagramContent);
      document.getElementById('diagram').innerHTML = svg;
      window.diagramRendered = true;
    } catch (error) {
      console.error('Mermaid render error:', error);
      window.renderError = error.message;
    }
  </script>
</body>
</html>
    `;

    await page.setContent(html);

    // Wait for the diagram to render
    console.log("Rendering diagram with icon packs...");
    await page.waitForFunction(
      () => window.diagramRendered === true || window.renderError,
      { timeout: 30000 },
    );

    // Check for errors
    const renderError = await page.evaluate(() => window.renderError);
    if (renderError) {
      throw new Error(`Mermaid render error: ${renderError}`);
    }

    // Get the SVG content and add white background matching viewBox
    const svgContent = await page.evaluate(() => {
      const svg = document.querySelector("#diagram svg");
      if (svg) {
        // Get viewBox dimensions
        const viewBox = svg.getAttribute("viewBox");
        if (viewBox) {
          const [x, y, width, height] = viewBox.split(" ").map(parseFloat);

          // Add white background to SVG matching viewBox
          const rect = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "rect",
          );
          rect.setAttribute("x", x);
          rect.setAttribute("y", y);
          rect.setAttribute("width", width);
          rect.setAttribute("height", height);
          rect.setAttribute("fill", "white");
          svg.insertBefore(rect, svg.firstChild);
        }
      }
      return svg ? svg.outerHTML : null;
    });

    if (!svgContent) {
      throw new Error("No SVG content generated");
    }

    // Write the SVG to file
    writeFileSync(join(__dirname, outputFile), svgContent);
    console.log(`✓ Successfully generated ${outputFile}`);
  } catch (error) {
    console.error("Error:", error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

renderMermaid();
