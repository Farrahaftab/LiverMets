const { chromium } = require('playwright');
(async () => {
  const [,, src, out] = process.argv;
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage();
  await p.goto('file://' + src, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({
    path: out, format: 'Letter', printBackground: true, displayHeaderFooter: true,
    margin: { top: '0.78in', bottom: '0.72in', left: '0.62in', right: '0.62in' },
    headerTemplate: '<div style="font-size:7pt;width:100%;padding:0 0.62in;display:flex;justify-content:space-between;font-family:Carlito,Calibri,sans-serif;color:#1F3A5F;letter-spacing:.08em"><span style="font-weight:700">SURVIVAL PREDICTION IN COLORECTAL LIVER METASTASES</span><span style="font-style:italic;letter-spacing:0">Final Draft for Supervisor Approval</span></div>',
    footerTemplate: '<div style="font-size:7pt;width:100%;text-align:center;font-family:Carlito,Calibri,sans-serif;color:#555">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
  });
  await b.close();
})();
