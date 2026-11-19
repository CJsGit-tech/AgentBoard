const path = require('node:path');
const frontend = path.resolve(__dirname, '../../../../../frontend');
const { defineConfig, devices } = require(path.join(frontend, 'node_modules/@playwright/test'));
module.exports = defineConfig({ testDir: path.join(frontend, 'tests'), timeout:30000, expect:{timeout:5000}, workers:1, fullyParallel:false, reporter:[['list'],['json',{outputFile:path.join(__dirname,'builder-playwright-results.json')}]], outputDir:path.join(__dirname,'builder-test-results'), use:{...devices['Desktop Chrome'],channel:'chrome',baseURL:'http://127.0.0.1:4203',viewport:{width:1600,height:1100},screenshot:'only-on-failure',trace:'retain-on-failure'}, webServer:{command:'npm run dev -- --port 4203',cwd:frontend,url:'http://127.0.0.1:4203',reuseExistingServer:true}});
