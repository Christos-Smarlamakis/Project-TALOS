# -*- coding: utf-8 -*-
"""
@Student: Christos Smarlamakis
std147661@ac.eap.gr, christossmarlamakis@gmail.com / 6945830515
"""

import numpy as np
import matplotlib.pyplot as plt

def plot_graph(benchmark_function, wolves_position_array, wolves_fitness, iteration_counter):
    """
    Απεικονίζει την γραφική παράσταση της συνάρτησης αξιολόγησης και τις θέσεις των λύκων κατα την σύγκλιση τους προς το βέλτιστο.
    """
    #Αποθήκευση του ολικού ελαχίστου στην μεταβλητή global_minimum.
    global_minimum = benchmark_function.get_fminimum_point()
    #Δημιουργία 3D Αξονα.    
    ax = plt.axes(projection='3d')
    #Αποθήκευση σε κατάλληλες μεταβλητές των ορίων της συνάρτησης.
    lower_bound, upper_bound = benchmark_function.lower_bound, benchmark_function.upper_bound
    #Δημιουγία πλέγματος των Αξόνων Χ1,Χ2.
    X1, X2 = np.linspace(lower_bound, upper_bound, 50), np.linspace(lower_bound, upper_bound, 50)    
    X, Y = np.meshgrid(X1, X2)
    #Υπολογισμός των τιμών της συνάρτησης για κάθε συντεταγμένη στο πλέγμα.
    Z = np.array([[benchmark_function.calculate_fitness([x, y]) for x, y in zip(row_x, row_y)] for row_x, row_y in zip(X, Y)])
    #Σχεδίαση της συνάρητησης αξιολόγησης
    ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.6)
    # Σχεδίαση των λύκων στον χώρο.
    ax.scatter3D(wolves_position_array[:, 0], wolves_position_array[:, 1], wolves_fitness, color='red', marker='o', label="Search agent")
    # Σχεδίαση του ολικού ελάχιστου.
    plt.scatter(global_minimum[0], global_minimum[1], color='blue', s=100, marker='+', label='Global Minimum')
    #Ρύθμιση της γωνίας προβολής του γραφήματος.
    ax.view_init(elev=30, azim=140)
    #Ορισμός Τίτλου και Ετικετών στους Αξονες.
    ax.set_title(f'{benchmark_function.name} function - Iteration {iteration_counter}')
    ax.set_xlabel('X1')
    ax.set_ylabel('X2')
    ax.set_zlabel('Fitness Value')    
    plt.legend(loc='upper right', prop={'size': 8})
    # Ενημέρωση του γραφήματος σε κάθε επανάληψη
    plt.pause(0.001)
    
    
def plot_top_view_graph(benchmark_function, wolves_position_array, iteration_counter):
    """
    Απεικονίζει την κάτοψη των λύκων και τη σύγκλισή τους προς το ολικό βέλτιστο.
    """
    #Αποθήκευση σε κατάλληλες μεταβλητές των ορίων και του ολικού βέλτιστου της συνάρτησης.
    lower_bound, upper_bound = benchmark_function.lower_bound, benchmark_function.upper_bound
    global_minimum = benchmark_function.get_fminimum_point()
    # Δημιουργία γραφήματος με μέγεθος 10x6.
    plt.figure(figsize=(10, 6))
    # Δημιουργία πλέγματος για τον άξονα X1 και X2.
    X1, X2 = np.linspace(lower_bound, upper_bound, 50), np.linspace(lower_bound, upper_bound, 50)
    X, Y = np.meshgrid(X1, X2)
    # Υπολογισμός τιμών της συνάρτησης για κάθε συντεταγμένη πάνω στο πλέγμα.
    Z = np.array([[benchmark_function.calculate_fitness([x, y]) for x, y in zip(row_x, row_y)] for row_x, row_y in zip(X, Y)])    
    plt.contourf(X, Y, Z, levels=50, cmap='viridis', alpha=0.6)
    plt.colorbar(label='Fitness Value')
    # Σχεδίαση των θέσεων των λύκων
    plt.scatter(wolves_position_array[:, 0], wolves_position_array[:, 1], color='red', s=50, label='Search agent')    
    # Σχεδίαση του ολικού ελάχιστου
    plt.scatter(global_minimum[0], global_minimum[1], color='blue', s=100, marker='+', label='Global Minimum')
    plt.title(f'{benchmark_function.name} function Top View- Iteration {iteration_counter}')    
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.legend(loc='upper right', prop={'size': 8})
    # Ενημέρωση του γραφήματος σε κάθε επανάληψη.
    plt.pause(0.001)
