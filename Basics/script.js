
//INTRODUCTION TO JAVA SCRIPT
// alert() shows a Popup

// console.log("Hello JavaScript");//prints output in the browser console

// //whern the browser reads <script src="script.js"></script> the javascript excuteion Happens


// alert("My Name is Swaroop");
// console.log("Im Learning JavaScript");
// alert("Welcome to FullStack develepment");
// all three execute in order

//Javascript is a Programing Language used to add Interactive and dynamic Behavior to the Web Pages
//Javascript can run without a Browser using The Node js
//----------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------

//LESSON 2:Execution Environment Statements and Comments

//Execution Environment : It is Simply a place where a Javascript code runs
//There are Two Main Environments .....Browser and Node js
//Browser has a JavaScript Engine(Chrome Uses V8 engine) that reads and executes the code
//Node js allows javascript to run outside the Browser

console.log("line1");
console.log("line2");
console.log("line3");
//JavaScript excecutes the code from top to bottom one statement at a time(Sequensital Execution)

//Whats is A Statement?
// ans : It Is a Single line instruction given to JavaScript
/*------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------*/

//LESSON 3: Variables(Var,let,const)
//Variable : it is a named container which stores the data

let name="Swaroop More";
let age=22;
let course="Masters in Computer application";

console.log("My Name is ",name);
console.log("Im ",age," years old");
console.log("Im Studying ",course);

course="MCA";
console.log("Course Changed To",course);


// const: means constant ie.. values cannot be reaasigned

const country="India";
console.log("Im from ",country);

//var: Old way of Creating Variables
//-----------------------------------------------------------------------------------------------------
//-------------------------------------------------------------------------------------------------


//LESSON 4 DataTypes
//it tells Javascript what type of value JavaScript Stores

let name1="Swaroop";//datatype is String
let age1=22;//datatype is Number
let isStudent=true;//BOOLEAN
let isteacher=false;//BOOLEAN
let marks;//undefined
let phone=null;//Variable has No Value

//Symbol : Creates A unique Value
let id=Symbol("id");

console.log(typeof name1);
console.log(typeof age);
console.log(typeof "Swaroop");
console.log(typeof 22);

//----------------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------------

//LESSON 5: Type Consversion

//1.String Concatenation
console.log("------------String Conactination------------------");
let age3="22";
console.log("Initial String :",age3);
console.log("After Concatenation :",age3 + 8);

console.log("hello"+"world");

console.log("10" + 20);//Output is 1020 ..It is called Implicit Type Conversion(Type Conversion)
//Implicit : Automatically changes one datatype into Another When Needed

console.log("10" - 5);//Here JavaScript converts 10 into a Number
console.log("10" * 5);
console.log("20" / 4);


//Explicit Type Conversion
//Instead Of JavaScript deciding the dataType...USer Decides the DataType

//1. Number():Converts a Value into a Number
let age4="45"
let newAge=Number(age4);
console.log("String :",age4);
console.log("Converted to Number :",newAge);

console.log("-----------------------------------------------");

//2. String :Converts A Value Into A String
let friend=45;

let newFriend=String(friend);
console.log("Number :",friend);
console.log("Converted to String :",newFriend);
console.log("--------------------------------------------------------------");


//Lesson5 : Operators

let a=20;
let b=30;
let result=a+b;
console.log("Addition is",result);

//Lesson 6 :Strings and String Functions
//Strings are Zero Indexed
console.log("-----String and String Functions---------");
let college=`MIT-WPU`;
console.log("Original String :",college);
console.log("Lenght of the String :",college.length);
console.log("Second letter in the String is",college[1]);
college=`Mit-World-Peace-University`;

console.log("UpperCase :",college.toUpperCase());
console.log("Lower Case :",college.toLowerCase());
college="Maharastra  institute Of Technology  ";
console.log(college.trim());
console.log(college.slice(0,4));


//Template Literals
console.log(`My name is ${name} and I am from ${college}`);
console.log(`  HI ${name}  Yor are from ${college} Congratulations `);


//Lesson 8 Arrays
//Collection Of Multiple Values Stored in a Single Variable

let fruits=["Apple", "Mango" ,"Banana"];
console.log(fruits);
console.log(fruits[0]);
fruits[1]="Orange";
console.log("Length Of Tha Array :",fruits.length);
console.log("Aceesing Last element using length -1",fruits[fruits.length-1]);

// Lessson 9: ARRAY METHODS
let numbersArr=[10,20,30,40,50,60];
console.log("Initial Array ",numbersArr);

numbersArr.push(70)
console.log("After adding Number at the end :",numbersArr);

numbersArr.pop();
console.log("After removing the Last element :",numbersArr);

numbersArr.unshift(5);
console.log("after adding number at the Beginning :",numbersArr);

numbersArr.shift()
console.log("After Removing The First Element ",numbersArr);


//Lesson : LOOPS 

//print numbers 1 to 5 using loop

for (let i=0;i<=5;i++){
    console.log(i);
}


for (let i=1; i<=10;i++){
    console.log(i);
}
console.log("------------------------------------------")


let n=1;
while( n!=20){
    console.log(n);
    n=n+1;
}

console.log("------------------------------");


let  i=10;
do{
    console.log(i);
}while(i<5);


let players=["Rohit","Virat","Iyer","Bumrah",45,18,13,93];

for (let i=0;i<players.length;i++){
    console.log(players[i]);
}

console.log("-------------------");
for (let i=5;i<=20;i++){
    if (i==10){
        break;
    }
    console.log(i);
}