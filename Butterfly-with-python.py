#!/usr/bin/python3
num = int(input('enter a number : '))
for i in range(1,num):
	if i <= num//2:
		print( '*' * i, ' ' * (num-i*2), '*' * i)
	else:
		print( '*' * (num-i), ' ' * (i*2 - num) , '*' * (num-i))
