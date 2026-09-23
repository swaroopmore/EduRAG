a=12
print("Identity or Memory Address",id(a))#Returns the identity of an Object ie the memory address in which the object is stored

numbers=[1,2,3,4]
print(id(numbers))
numbers.append(5)
print(id(numbers))