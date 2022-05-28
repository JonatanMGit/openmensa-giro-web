const puppeteer = require('puppeteer');
const discord = require('discord.js');
// add intents
const client = new discord.Client({ intents: [discord.Intents.FLAGS.GUILDS] });


const password = 'x';
const username = 'x';
client.login("x");

function sleep(time) {
  return new Promise(function (resolve) {
    setTimeout(resolve, time)
  });
}

client.on('ready', () => {
  console.log('I am ready!');
});

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768 });
  await page.goto('https://fvsg-steinwerk.giro-web.de/');

  // type admin into document.querySelector("#loginname")
  await page.type('#loginname', password);
  // type admin document.querySelector("#passwort > input[type=password]")
  await page.type('#passwort > input[type=password]', username);
  // press document.querySelector("#anmelden_button")
  await page.click('#anmelden_button');

  await sleep(1000);
  // edit #header > span text
  await page.evaluate(() => {
    document.querySelector('#header > span').innerText = 'PeePeePooPoo';
    document.querySelector("#topnav > span").innerText = 'Joe Bidne\nGuthaben: 1Billion';
  })
  // grab a screenshot and send it to a discord channel with the id 799701208607752194
  let screenshot = await page.screenshot();
  await browser.close();
  // send the screenshot to the discord channel
  // client.channels.cache.get('799701208607752194').send({ files: [{ attachment: screenshot, name: 'peepee.png' }] });
})();

