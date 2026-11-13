import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

v = np.array([9, 10])

C = A + B
D = A - B
E = A * B
F = np.dot(A, B)
G = A @ B
H = A.T
I = np.linalg.inv(A)
J = np.linalg.det(A)
K = np.dot(A, v)
L = np.linalg.solve(A, v)

print("C (A + B):\n", C, "\n")
print("D (A - B):\n", D, "\n")
print("E (Element-wise A * B):\n", E, "\n")
print("F (Matrix Product np.dot(A, B)):\n", F, "\n")
print("G (Matrix Product A @ B):\n", G, "\n")
print("H (Transpose A.T):\n", H, "\n")
print("I (Inverse of A):\n", I, "\n")
print("J (Determinant of A):", J, "\n")
print("K (Matrix-Vector Product A * v):", K, "\n")
print("L (Solve Ax = v for x):", L)