//DOM : JavaScript Starts Controlling HTML and CSS
//Document Object Model
//Document : The HTML Page
//Object : JavaScript treats every HTML element as an Object
//Model : It is a Simply a representation
//The Browser Converts HTML into a Tree Like Structure
//That Structure is called the DOM Tree
//Every HTML tag becomes a Node


console.log("Dom Loaded Successfully");
//alert("Welcome to DOM Implementation");

let heading=document.getElementById("heading");
console.log("Heading Of the Webpage is :",heading);

let firstpara=document.getElementById("firstpara");
console.log("First Paragraph :",firstpara);

//If Id Doesnt exists the Output will be Null
//Id Must Be Unique


//Getting elements by Class Name

let skills=document.getElementsByClassName("skill");
console.log("Skills :",skills);

console.log(skills[2]);
console.log("First Skill",skills[0]);
console.log("fourth Skill ",skills[3]);


//Getting Elements By Tag Name

let legend=document.getElementsByTagName("legend");
console.log("Legend Tag Info :",legend);

let para=document.getElementsByTagName("p");
console.log("Paragraphs :",para);

//Query Selector ;One of the DOM Methods
//It Returns The First matching element

//Select by ID
let heading1=document.querySelector("#heading");
console.log(heading1);


//Select by ID
let button=document.querySelector("#firstbut");
console.log(button);

//Select By Class
let skills1=document.querySelector(".skill");
console.log(skills1);

//select by Tag
let tag=document.querySelector("button");
console.log(tag);

let tag1=document.querySelector("legend");
console.log(tag1);

//QuerySelectorAll()
//Returns all Matching elements

let skills2=document.querySelectorAll("#skl");
console.log(skills2);


let class1=document.querySelectorAll(".skill");
console.log(class1);

//Accessing The Elements
console.log(class1[0]);
console.log(class1[1]);
console.log(class1[2]);
console.log(class1[3]);


for (let sk of class1){
    console.log(sk);
}


//InnerText: It Gets or Changes the Visible text of an element
const headingele=document.getElementById("heading");
console.log(headingele.innerText);

const par=document.getElementById("firstpara");
console.log(par.innerText);

//Changing The Text
const headingchange=document.getElementById("heading");
headingchange.innerText="Resume of More Swaroop";

const nameclg=document.getElementById("nameclg");
nameclg.innerText="College Information";

const infoclg=document.getElementById("info");
infoclg.innerText="Maharashtra Institute Of Technology (MIT-WPU)";

const changepara=document.getElementById("firstpara");
changepara.innerText="This Resume was Updated Using JavaScript";

//TextContent
//Returns all text,even if it is Hidden with Css


//innerHTML
//It reads or changes the HTML inside an element not just the Text


const colo=document.getElementById("heading");
console.log(colo.innerHTML);

colo.innerHTML="<h2> Swaroop More Resume</h2>";

const skills4=document.getElementById("skl");
skills4.innerHTML +="<li>React Js</li>";