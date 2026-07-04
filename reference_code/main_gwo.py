# -*- coding: utf-8 -*-
"""
@Student: Christos Smarlamakis
std147661@ac.eap.gr, christossmarlamakis@gmail.com / 6945830515
"""

import csv
import os
from benchmark_function import BenchmarkFunction
from gwo import GWO


# Ορισμός παραμέτρων
benchmark_functions_names_list = ["ackley", "griewank", "rastrigin", "rosenbrock", "sphere", "dejongF5_foxholes", "goldstein-price"]
#benchmark_functions_names_list = ["dejongF5_foxholes", "goldstein-price"]
dimensions_number = 2
wolves_number = 30
max_iteration_num = 100
min_fitness_standard_deviation = 1e-10
runs = 1
plot_graph_enabled = 1  # True/1 ή False/0 για εμφάνιση ή μή του γραφήματος.

# Δημιουργία φακέλου αποθήκευσης αν δεν υπάρχει
results_folder = f"cli_results\\results_with_{wolves_number}_agents_cli"
os.makedirs(results_folder, exist_ok=True)

# Εκτελούμε τον αλγόριθμο για όλες τις συναρτήσεις δοκιμής στην σειρά και αποθηκεύουμε τα αποτελέσματα για στατιστική ανάλυση σε αρχεία csv.
for benchmark_function_name in benchmark_functions_names_list:

    # Αν η συνάρτηση είναι από τις dejongF5_foxholes ή goldstein-price, ορίζουμε τις διαστάσεις σε 2.
    if benchmark_function_name in ["dejongF5_foxholes", "goldstein-price"]:
        dimensions = 2
    else:
        dimensions = dimensions_number

    benchmark_function = BenchmarkFunction(benchmark_function_name, dimensions) #Δημιουργούμε ενα αντικείμενο BenchmarkFunction
    results_list = []
    
    print(f"{benchmark_function_name} function:")
    for i in range(runs):        
        print(f"Run {i+1}/{runs}")
        #Εκτέλεση του Αλγορίθμου GWO με τις επιλεχθείσες παραμέτρους και επιστροφή των αποτελεσμάτων στο λεξικό results_dictionary
        results_dictionary = GWO(wolves_number, max_iteration_num, min_fitness_standard_deviation, benchmark_function, plot_graph_enabled)
        results_dictionary['run'] = i+1
        results_list.append(results_dictionary)
        
    # Ορισμός διαδρομής αποθήκευσης αρχείου
    csv_filename = os.path.join(results_folder, f"gwo_results_{benchmark_function_name}.csv")    
    
    # Αποθήκευση των αποτελεσμάτων σε CSV.
    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames = ['run', 'min_fitness', 'mean_fitness', 'alpha_wolf_position', 'alpha_wolf_fitness', 'global_minimum_value', 'fitness_standard_deviation', 'positional_deviation', 'iterations', 'gwo_time'], delimiter=';')
        writer.writeheader()
        writer.writerows(results_list)    
    
    print(f"Results saved in {csv_filename}\n")

