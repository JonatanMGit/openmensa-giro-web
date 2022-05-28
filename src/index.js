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

  // grab the text from #menuorder > tbody > tr:nth-child(1) > th:nth-child(2) > div and #menuorder > tbody > tr:nth-child(1) > th:nth-child(3) > div
  let text = await page.evaluate(() => {

    // repeat for each day of the week
    var text = []
    for (let i = 2; i <= 6; i++) {
      text.push([document.querySelector('#menuorder > tbody > tr:nth-child(1) > th:nth-child(' + i + ') > div').innerText.replace(/[\n\r]/g, '')]);
    }
    // add a array to each array element
    for (let i = 0; i < text.length; i++) {
      text[i].push([])
    }

    for (let day = 2; day <= 6; day++) {
      for (let meal = 2; meal <= 4; meal++) {
        try {
          text[day - 2][1].push(document.querySelector('#menuorder > tbody > tr:nth-child(' + meal + ') > td:nth-child(' + day + ') > div > span.description').innerText.replace(/[\n\r]/g, ''));
        } catch (e) {
          text[day - 2][1].push("");
        }
      }
    }



    return text;
  });


  console.log(text);



  // await browser.close();
  // send the screenshot to the discord channel
  // client.channels.cache.get('799701208607752194').send({ files: [{ attachment: screenshot, name: 'peepee.png' }] });
})();

