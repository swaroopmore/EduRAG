//Lesson 11 Functions
// a Function is a Resuable Block of Code

function sayHello(){
    console.log("Hello JavaScript");
}

sayHello();

for(let i=0;i<6;i++){
    console.log(sayHello());
}

//ANother Example of Function

console.log("Start");
function greet(){
    console.log("Inside Function Text");
}

console.log("Before Calling Function");

for (let i=0;i<=3;i++){
    console.log(greet());
}


// Function with Parameters

function add(n1,n2){
    result=n1+n2;
    console.log("Addition is",result);

}

add(12,24);


function Multi(num1,num2){
    return num1*num2;//Return Stops The Function
}

let res=Multi(12,2);
console.log(res);

//Function Expression
//Functions can also be stored inside a Variable

const greet1=function(){
    console.log("Hello Swaroop More");
}
greet1();


const add1=function(num1,num2){
    result3=num1+num2;
    console.log("Addition Is :",result3);
}

add1(34,16);

const mult=function(num1,num2){
    return num1*num2;
}

console.log(mult(12,10));

//Anonymous Function
// Means A Function Without a name



//Arrow Functions...Introduced in ES6
//They Provide a Shorter Syntax
const sub=(num1,num2) =>{
    result=num1-num2;
    console.log("Substraction is :",result);
}

sub(100,34);

// short Arrow Function
const square=num => num * num;
console.log(square(6));

const sayHey=name =>{
    console.log(name);

}

sayHey("Swaroop");


//objects :An Object is a collection of related data stored as key-value pairs.
let student2 = {

    name : "Swaroop",

    age : 22

};

let laptop = {

    brand : "Lenovo",

    ram : "16GB",

    price : 65000

};

//Accessing Object Properties
console.log(laptop.brand);
delete student2.age;
console.log(student2);



//Objecs can aslo Store Functions
//Functions inside objects are called Methods


let players23={

    name:"Swaroop More",

    jersey_no :45,

    team:"India",

    greet: function(){
        console.log("Hello World");
    }
};

players23.greet();


let std={
    name:"Bhumika Madhwani",
    prn:"1272250168",

    add: function(num1,num2){
        result=num1+num2;
        console.log(result);

    }
};

std.add(12,45);

//this keyword: refers to the object that is calling the method


let teacher={
    name:"Sangeeta D",
    subject:"Data Communication and Security",
    class:"FYMCA",
    greet: function(){
        console.log(this.subject);
    }
};

teacher.greet();


//Nested Objects: Objects can contain Other Objects

let tenant={
    name:"Ujwal Amodkar",
    age:23,

    address:{
        city:"Pune",
        state:"Maharashtra",
        lang:"Marathi"
    },

    rent_month:["January","February","March","April"]
};

console.log(tenant.address.city);
console.log(tenant.address.state);
console.log(tenant.rent_month);

console.log(Object.keys(tenant));//Returns all Properties Names
console.log(Object.values(tenant));//returns all values
console.log(Object.entries(tenant));//returns both keys and values

//ES6: needed in react,node.js.next.js,Express

let number1=45;
let number2=65;
console.log(`Sum =${number1 + number2}`);

console.log(`Multiline strings
    Hello World from Swaroop
    Haha That The Game brother`);


//Destructuring

let {name,age}=tenant;
console.log(name);
console.log(age);


//Array Destructuring
let colors=["Orange","Red","Blue","Yellow","Green"];

let [first,second,,,fifth]=colors;

console.log(first);
console.log(second);
console.log(fifth);

//Spread Operator
//(...) three dots sometimes it is Spread Operator and Sometimes it is Rest Operator
//Spread Operator exapands an array or object into Individual Elements

console.log(...colors);

//Copying Arrays
let arr1=[1,2,3,4,5];
let arr2=[...arr1];
arr2.push(6);
console.log(arr1);
console.log(arr2);

//Merging Arrays
let frontend = [

"HTML",

"CSS"

];

let backend = [

"Node",

"MongoDB"

];

let fullStack = [

...frontend,

...backend

];

console.log(fullStack);

//Spread with Objects

let roomi={
    name:"Ankush Deshmukh",
    company:"Indio Networks"
}

let updated_roomi={
    ...roomi,
    city:"Akola",
    Lang:"Marathi"
}
console.log(updated_roomi);


// Rest Operator : Collect Multiple Values Into One Variable
function aded(...numbers){

console.log(numbers);

}

aded(10,20,30,40);

//Sum using Rest Operator

function hihi(...numbers){
    let total=0;

    for (let num of numbers){
        total +=num;
    }
    return total;
}

console.log(hihi(23,45,12));
console.log(hihi(654,213,574));