const path = require("path");
const express = require("express");
const bodyParser = require("body-parser");
const app = express();

if (process.argv.length !== 3) {
    console.log("Usage: summerCampServer.js portNumber");
    process.exit(0);
}

require("dotenv").config({
   path: path.resolve(__dirname, ".env"),
});

const uri = process.env.MONGO_CONNECTION_STRING;
const dbAndCollection = {db: "summerCamp", collection: "applicants"};
const { MongoClient, ServerApiVersion } = require("mongodb");

/* Defining the view/templating engine to use */
app.set("view engine", "ejs");

/* Directory where templates will reside */
app.set("views", path.resolve(__dirname, "templates"));

/* Initializes request.body with post information */ 
app.use(bodyParser.urlencoded({extended:false}));

app.get("/", (request, response) => {
    /* Generating the HTML using welcome template */
    response.render("index");
});

const portNumber = Number(process.argv[2]);

app.get("/apply", (request, response) => {
    response.render("apply", {portNumber: portNumber});
});

app.post("/processApplication", (request, response) => {
    
    const name = request.body.name;
    const email = request.body.email;
    const gpa = request.body.gpa;
    const info = request.body.backgroundInformation;
    const applicant = {
        name: name,
        email: email,
        gpa: gpa,
        info: info
    };
    
    (async () => {
        const client = new MongoClient(uri, {serverApi: ServerApiVersion.v1});
        try {
            await client.connect();
            const database = client.db(dbAndCollection.db);
            const collection = database.collection(dbAndCollection.collection);
            
            await collection.insertOne(applicant);
        } catch (e) {
            console.error(e);
        } finally {
            await client.close();
        }
    })();
    response.render("processApplication", applicant);
});

app.get("/reviewApplication", (request, response) => {
    response.render("reviewApplication", {portNumber: portNumber});
});

app.post("/processReviewApplication", (request, response) => {
    const email = request.body.email;

    (async () => {
        const client = new MongoClient(uri, {serverApi: ServerApiVersion.v1});
        try {
            await client.connect();
            const database = client.db(dbAndCollection.db);
            const collection = database.collection(dbAndCollection.collection);

            let filter = {email: email};
            
            result = await collection.findOne(filter);
            if (result === null) {
                const applicant = {
                    name: "NONE",
                    email: "NONE",
                    gpa: "NONE",
                    info: "NONE"
                };
                response.render("processReviewApplication", applicant);
                return;
            } else {
                const applicant = {
                    name: result.name,
                    email: result.email,
                    gpa: result.gpa,
                    info: result.info
                };
            response.render("processReviewApplication", applicant);
            }
        } catch (e) {
            console.error(e);
        } finally {
            await client.close();
        }
    })();
});

app.get("/adminGPA", (request, response) => {
    response.render("adminGPA", {portNumber: portNumber});
});

app.post("/processAdminGPA", (request, response) => {

    const gpa = request.body.gpa;
    
    (async () => {
        const client = new MongoClient(uri, {serverApi: ServerApiVersion.v1});
        try {
            await client.connect();
            const database = client.db(dbAndCollection.db);
            const collection = database.collection(dbAndCollection.collection);

            let filter = {gpa: {$gte: gpa}};
            
            const cursor = collection.find(filter);
            const applicants = await cursor.toArray();

            let table = "<table border='1'><tr><th>Name</th><th>GPA</th></tr>";

            applicants.forEach((applicant) => {
                table += `<tr><td>${applicant.name}</td><td>${applicant.gpa}</td></tr>`;
            });
            table += "</table>";

            response.render("processAdminGPA", {gpaTable: table});
        } catch (e) {
            console.error(e);
        } finally {
            await client.close();
        }
    })();
});

app.get("/adminRemove", (request, response) => {
    response.render("adminRemove", {portNumber: portNumber});
});

app.post("/processAdminRemove", (request, response) => {
    (async () => {
        const client = new MongoClient(uri, {serverApi: ServerApiVersion.v1});
        try {
            await client.connect();
            const database = client.db(dbAndCollection.db);
            const collection = database.collection(dbAndCollection.collection);
            const result = await collection.deleteMany({});

            response.render("processAdminRemove", {numberRemoved: result.deletedCount});
        } catch (e) {
            console.error(e);
        } finally {
            await client.close();
        }
    })();
});

app.listen(portNumber);
console.log(`Web server started and running at http://localhost:${portNumber}`);
process.stdout.write("Stop to shut down the server: ");
process.stdin.setEncoding("utf8");
process.stdin.on('data', (dataInput) => {
    const command = dataInput.trim().toLowerCase();
    if (command === "stop") {
        console.log("Shutting down the server");
        process.exit(0);
    } else {
        console.log("Invalid command: " + command);
        process.stdout.write("Stop to shut down the server: ");
    }        
})