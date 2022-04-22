const puppeteer = require('puppeteer');
const config = require('config');
const args = require('yargs').argv;
var usern = config.get('user_details.username');
var passwd = config.get('user_details.password');
if (process.env.PDF_DOWNLOAD_USER) {
    usern = process.env.PDF_DOWNLOAD_USER;
    passwd = process.env.PDF_DOWNLOAD_PASS;
}
var origin = null;
var url = null;
var file_name = 'report';
var width = 1024;
var height = 1024;

async function wait(ms) {
	return new Promise(resolve => {
	  setTimeout(resolve, ms);
	});
}
//We are passing 3 arguments, other three are default arguments of any node script invocation
if (process.argv.length === 6) {
	url = process.argv[2];
	file_name = process.argv[3];
	tab_selector_id = process.argv[4];
	origin = process.argv[5];
	// console.info(tab_selector_id);
	// console.info(file_name);
}

if(url && origin) {
(async () => {
		const browser = await puppeteer.launch({headless: true, devtools: true,defaultViewport: null, args: ['--no-sandbox','--start-maximized']});
		const page = await browser.newPage();
		let login_url = origin + "/login/";
		try {
			await page.goto(login_url);
			//TODO: Append your own credentials here of the user which has at least read access to all the dashboards
			await page.type('#username',usern);
				await page.type('#password',passwd);
			let selector = '#loginbox > div > div.panel-body > form > div:nth-child(4) > div > div > input';
				await Promise.all ([
						await page.click(selector)
				]);
				console.info('Authenticated');
		}
		catch (error) {
			console.error(error);
			process.exit(1);
		}
		//await page.waitForNavigation();
		const cookies = await page.cookies();
		await page.close();
		const page2 = await browser.newPage();
		await page2.setViewport({ width: 1366, height: 768});
		await page2.setCookie(...cookies);
		//WE will send the url of the dashboard which the client / service want to print here
		//And also authenticate whether the user is allowed to see that data or not before making this call
		await page2.goto(url,{waitUntil: "networkidle2"});

		var pdf_dimensions = await page2.evaluate(() => {


				let pdf_dim = [];
				pdf_dim.push(document.body.scrollWidth);
				pdf_dim.push(document.body.scrollHeight);
				return pdf_dim;
		});

		console.info(pdf_dimensions);


		if(tab_selector_id !== "Null") {

			let tab_to_click = '#'+tab_selector_id+"> div > div > div > span.editable-title > input[type=button]";
			await page2.click(tab_to_click);

		}


		let div_tab_header = "#app > div > div:nth-child(1) > div.dragdroppable.dragdroppable-column > div > div.with-popover-menu > div > div";
		let div_header_to_remove= ".dashboard-header";
			await page2.evaluate((selheader,seltab) => {
				let header = document.querySelectorAll(selheader);
				let tab_header = document.querySelectorAll(seltab);
				//console.log(tab_header);
				for(let i=0; i< tab_header.length; i++){
					tab_header[i].parentNode.removeChild(tab_header[i]);
				}
				let tabs = document.querySelectorAll('*[id^="GRID_ID-pane"]');
				for(let i=0; i< header.length; i++){
					header[i].parentNode.removeChild(header[i]);
					//console.log(header[i])
				}

			}, div_header_to_remove, div_tab_header);
			let width = pdf_dimensions[0];
			let height = pdf_dimensions[1];

			let file_path = '../../static/reports/'+file_name.concat('.pdf');
			// Waiting for the page to be loaded in the dom
			await wait(10000);
			try {
				await page2.pdf({
						path: file_path,
						height: height,
						width: width,
						printBackground: true,
						preferCSSPageSize: true,
					});
			}
			catch (error) {
				console.error(error);
				process.exit(1);
			}
			await page2.close();
			await browser.close();
			console.info("Pdf Downloaded");


})().then(() => {console.info("Done"); process.exit(0)});
}
else {
	process.exit(1);
}
