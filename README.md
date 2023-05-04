# Garbled Circuit
Project for the Introduction to Cybersecurity course. The aim is to develop an Yao's Protocol implementation[^fn3]; we will use it to sum two sets of values.  

In this project, as already written, the function used is the 8-bit sum. The circuit is represented in the above figure.

| <img src="src/images/8-bit_full_adder.png" width="2000"> |
|:--:|
| <b>Circuit </b>|

It is made of two components: Half adder and full adder.

Half adder is used to sum the right-most digit of the number.

| <img src="src/images/Half_adder.png" width="2000"> |
|:--:|
| <b>Half Adder </b>|

Full adder is used to sum a generic digit in the number, ranging from position 1 to 8. It receives in input also carry of the previous sum.

| <img src="src/images/Full-adder.png" width="2000"> |
|:--:|
| <b>Full Adder</b>|

Alice and Bob have two sets of numbers (given by the user), they compute the sum of this set on their own. Then they execute the secure sum of their
set's sum using Yao's protocol.





[comment]: <> (Citations)

[^fn3]: [Wik21b] Wikipedia contributors. Secure two-party computation — Wikipedia,
The Free Encyclopedia. [Online; accessed 20-January-2022]. 2021.
