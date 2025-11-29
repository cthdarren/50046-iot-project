# Mermaid Diagram Export with Icon Packs

This directory contains a custom rendering solution for Mermaid diagrams with icon pack support (AWS Logos from Iconify).

## Quick Start

```bash
npm install
npm run export
```

This will read `system-diagram.mmd` and generate `system-diagram.svg` with all AWS icons properly embedded.

## How It Works

The `render.js` script uses Puppeteer to:

1. Launch a headless Chrome browser
2. Create an HTML page with Mermaid loaded from CDN
3. Register the Iconify `logos` icon pack
4. Render your diagram with all icons properly loaded
5. Extract the SVG and save it to a file

This approach ensures that icon packs are registered before rendering, which is necessary for icons to appear in the output.

## Files

- **`system-diagram.mmd`** - Your mermaid diagram source file
- **`render.js`** - Custom Puppeteer script that renders diagrams with icon packs
- **`system-diagram.svg`** - Generated output (created after running `npm run export`)

## Current Diagram

The diagram (`system-diagram.mmd`) shows an AWS architecture with:

- **API** group (AWS Lambda) containing:
  - Database (AWS Aurora)
  - Storage (AWS Glacier)
  - Storage (AWS S3)
  - Server (AWS EC2)
- Connections between services

## Customization

### Change Output Format

To export as PNG instead of SVG, modify `render.js`:

1. Change the `outputFile` extension to `.png`
2. Replace the SVG extraction code with:

```javascript
await page.screenshot({ 
  path: join(__dirname, outputFile),
  clip: await page.evaluate(() => {
    const svg = document.querySelector('#diagram svg');
    const box = svg.getBoundingClientRect();
    return { x: box.x, y: box.y, width: box.width, height: box.height };
  })
});
```

### Add More Icon Packs

To include additional Iconify icon packs, update the `registerIconPacks` array in `render.js`:

```javascript
mermaid.registerIconPacks([
  {
    name: 'logos',
    loader: () =>
      fetch('https://cdn.jsdelivr.net/npm/@iconify-json/logos@1/icons.json')
        .then(res => res.json())
  },
  {
    name: 'mdi', // Material Design Icons
    loader: () =>
      fetch('https://cdn.jsdelivr.net/npm/@iconify-json/mdi@1/icons.json')
        .then(res => res.json())
  }
]);
```

Browse available icon packs at [Iconify](https://icon-sets.iconify.design/).

### Update the Diagram

Edit `system-diagram.mmd` with your Mermaid syntax. The render script will automatically process it.

## Dependencies

- **`puppeteer`** - Headless browser for rendering diagrams
- **`@iconify-json/logos`** - AWS and tech company logos icon pack

Mermaid is loaded from CDN at render time, so no local installation is needed.

## Troubleshooting

### Render Timeout

If your diagram is complex and times out, increase the timeout value in `render.js`:

```javascript
await page.waitForFunction(
  () => window.diagramRendered === true || window.renderError,
  { timeout: 60000 } // Increase from 30000 to 60000
);
```

### Linux Browser Issues

On Linux, if Chrome fails to launch, install additional dependencies:

```bash
# Debian/Ubuntu
sudo apt-get install -y libgbm-dev ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils
```

The script already includes `--no-sandbox` and `--disable-setuid-sandbox` flags for compatibility.

### Icons Not Showing

Icons load from the Iconify CDN at render time. Ensure you have an active internet connection when running `npm run export`.