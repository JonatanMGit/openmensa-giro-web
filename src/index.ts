import axios from "axios";
import * as cheerio from 'cheerio';

// fetch https://fvsg-steinwerk.giro-web.de/index.php and grab #loginform > input[type=hidden]:nth-child(1)


async function main() {
	var res = await axios.get("https://fvsg-steinwerk.giro-web.de/index.php", { withCredentials: true })
	const $ = cheerio.load(res.data)
	var proc = $("#loginform > input[type=hidden]:nth-child(1)").val()
	var logidpost = $("#loginform > input[type=hidden]:nth-child(2)").val()
	console.log("proc: " + proc);
	console.log("logidpost: " + logidpost)
	var ses1 = res.headers["set-cookie"][0].split(";")[0]

	const params = new URLSearchParams();
	params.append('proc"', proc);
	params.append('logidpost', logidpost);
	params.append('loginame', "xx");
	params.append('loginpass', "xx");
	var res2 = await axios.post("https://fvsg-steinwerk.giro-web.de/index.php", params, {
		withCredentials: true,
		headers: {
			"Cookie": ses1 + "; " + res.headers["set-cookie"][1].split(";")[0],
			'Content-Type': 'application/x-www-form-urlencoded'
		}
	})
	var ses2 = res2.headers["set-cookie"][0].split(";")[0]
	var res3 = await axios.get("https://fvsg-steinwerk.giro-web.de/index.php", {
		withCredentials: true,
		headers: {
		"Cookie": ses2 + "; " + res.headers["set-cookie"][1].split(";")[0],
	}
	})
	console.log(res3.data)
	

}
main();