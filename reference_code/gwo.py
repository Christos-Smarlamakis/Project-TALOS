# -*- coding: utf-8 -*-
"""
@Student: Christos Smarlamakis
std147661@ac.eap.gr, christossmarlamakis@gmail.com / 6945830515
"""

import numpy as np
from scipy.stats import uniform
import concurrent.futures as cf
from time import perf_counter
import plot_graph as plot


def find_best_three_wolves(wolves_positions_array, benchmark_function, iteration_counter, plot_graph_enabled, gui_callback=None, stop_event=None):
    """
    Η συνάρτηση εντοπίζει απο το σύνολο των πρακτόρων τους τρείς καλυτερους με βάση την τιμή της καταλληλότητας.
    
    Αρχικά δέχεται ως ορίσματα έναν πίνακα με τις θέσεις όλων των πρακτόρων, την συνάρτηση αξιολόγησης, τον αριθμό της τρέχουσας επανάληψης
    και μία σημαία για την εμφάνιση ή μη γραφικής παράστασης. Επιστρέφει ένα λεξικό με τις θέσεις και τις καταλληλότητες των ηγετών λύκων,
    την τυπική απόκλιση των καταλληλοτήτων και τέλος τις τιμές των fitness όλων των λύκων.
    
    Args:
        wolves_positions_array (numpy.ndarray): Πίνακας NumPy διαστάσεων (Ν, D) με τις θέσεις των Ν λύκων στον χώρο αναζήτησης D διαστάσεων.
        benchmark_function (object): Η συνάρτηση αξιολόγησης.
        iteration_counter (int): Ο αριθμός της τρέχουσας επανάληψης.
        plot_graph_enabled (bool): Σημαία για την εμφάνιση γραφήματος ανα 20 επαναλήψεις αν το πρόβλημα ειναι 2D.
        
    Returns:
        dict: Λεξικό με τους τρεις καλύτερους λύκους (θέση και fitness).
        float: Τυπική απόκλιση των τιμών καταλληλοτήτων του πληθυσμού που αποτελεί δείκτη σύγκλιση του αλγορίθμου στο ολικό βέλτιστο.
        numpy.ndarray: Πίνακας NumPy με τις τιμές καταλληλότητας όλων των λύκων.  
    """
    # Αρχικοποίηση του λεξικού για τους καλύτερους λύκους alpha, beta και delta.
    # Τα κλειδιά για τους λύκους είναι το 0 : alpha, 1 : beta, 2 : delta.
    # Η τιμή του κάθε κλειδιού είναι μία λίστα με δύο στοιχεία, το διάνυσμα της θέσης του λύκου και η καταλληλότητα του (αρχική τιμή άπειρο-inf).
    best_wolves_dictionary = {      
                                0 : [np.zeros(wolves_positions_array.shape[1]), float("inf")], #[[0.0,...,0.0],inf]
                                1 : [np.zeros(wolves_positions_array.shape[1]), float("inf")], #[[0.0,...,0.0],inf]
                                2 : [np.zeros(wolves_positions_array.shape[1]), float("inf")]  #[[0.0,...,0.0],inf]
                             }
     
        
    # Υπολογισμός καταλληλοτήτων των λύκων με παράλληλη εκτέλεση χρησιμοποιούμε το with..as.. για αποφυγή διαρροών μνήμης και αυτόματο κλείσιμο του executor.
    with cf.ThreadPoolExecutor() as executor:
        # Με την Map() εκτελείται η συνάρτηση calculate_fitness() σε κάθε στοιχείο του wolves_positions_array.
        # ακολούθως με την list() μετατρέπεται σε λίστα ο iterator που επιστρέφεται απο την Map() με τα δεδομένα.
        wolves_fitness_list = list(executor.map(benchmark_function.calculate_fitness, wolves_positions_array))            
    
    # Μετατροπή της λίστας με τις καταλληλότητες των λύκων σε numpy array για ευκολία στους υπολογισμούς.
    wolves_fitness_numpy_array = np.array(wolves_fitness_list)  
    #Η Np.argsort() επιστρέφει μία λίστα με τους δείκτες της λίστας που αν αντιστοιχηθούν σε τιμές θα προκύψει η αυξουσα ταξινομημένη διάταξη των τιμών.
    sorted_indices = np.argsort(wolves_fitness_numpy_array)
    #Πραγματοποιείται λήψη με indexing απο την λίστα sorted_indices[] των τριών πρώτων στοιχείων που αποτελούν και τα Index του πίνακα wolves_positions_array[] με τις μικρότερες τιμές του fitness.
    #και άρα τις καταλληλότητες των τριών ηγετών λύκων. Ακολούθως αποθηκευόυμε σε ένα λεξικό τις θέσεις και τις καταλληλότητες των τριών καλυτερων λύκων.
    for i in range(3):
        best_wolves_dictionary[i] = [wolves_positions_array[sorted_indices[i]], wolves_fitness_numpy_array[sorted_indices[i]]]
    
    #Σε περίπτωση που δεν γίνεται εκτέλεση του αλγορίθμου απο το Γραφικό Περιβάλλον σχεδιάζουμε την γραφική παράσταση με τις θέσεις των λύκων.
    if gui_callback is None:
        # Αν το πρόβλημα είναι δισδιάστατο (2D) εμφανίζεται ανα 20 επαναληψεις το γράφημα της συνάρτησης με τις θέσεις των λύκων και την θέση του ολικού βέλτιστου (ελαχίστου).
        if benchmark_function.dimensions == 2 and iteration_counter % 10 == 0 and plot_graph_enabled == True:
           plot.plot_graph(benchmark_function, wolves_positions_array, wolves_fitness_numpy_array, iteration_counter)
           #Αφαιρώντας το σχόλιο απο την κάτωθι γραμμή δύναται να απεικονιστεί και η κάτοψη του γραφήματος.
           #plot.plot_top_view_graph(benchmark_function,wolves_positions_array,iteration_counter).  
    
    # Υπολογισμός της τυπικής απόκλισης της καταλληλότητας των λύκων.
    fitness_standard_deviation = np.std(wolves_fitness_numpy_array)    
    #Επιστροφή λεξικού ηγετών λύκων, τυπικής απόκλισης καταλληλοτήτων και πίνακα καταλληλοτήτων όλων των λύκων. 
    return best_wolves_dictionary, fitness_standard_deviation, wolves_fitness_numpy_array

def calculate_new_position(best_wolves_dictionary, wolf_position, a, dimension):
    """    
    Η μέθοδος υπολογίζει τις νέες θέσεις των λύκων με βάσει τις θέσεις των τριών καλύτερων λύκων. 
    
    Υπολογίζει τους τυχαίους συντελεστές r1,r2 και τις παραμέτρους A, C για να καθορίσει την σύγκλιση ή οχι των υπόλοιπων λύκων.
    προς τους τρεις ηγέτες λύκους, εν συνεχεία υπολογίζει τη νέα θέση του κάθε λύκου στη τρέχουσα διάσταση ως το μέσο όρο των θέσεων των τριών ηγετών λύκων.        
        
    Args:
        best_wolves_dictionary (dict): Λεξικό με θέσεις και fitness των 3 καλύτερων λύκων.
        wolf_position (float): Η τρέχουσα θέση του λύκου στη συγκεκριμένη διάσταση.
        a (float): Συντελεστής a που ισορροπεί την εξερεύνηση και την εκμετάλλευση του GWO.
        dimension (int): Η τρέχουσα διάσταση.

    Returns:
        float: Η νέα θέση του λύκου στη συγκεκριμένη διάσταση.      
    """     
    # Για κάθε διάσταση υπολογίζονται οι δύο τυχαία συντελεστές r1,r2 με ομοιόμορφη κατανομή που καθορίζουν την  ένταση και την κατεύθυνση της αναζήτησης - εξερέυνησης (exploration).
    r1, r2 = uniform.rvs(size=2) #Επιστροφή δύο τυχαίων αριθμών στο [0,1] με ομοιόμορφη κατανομή (ισοπιθανοι).     
    A = 2 * a * r1 - a #Υπολογισμός παραμέτρου Α που σχετίζεται με την απόφαση συνέχισης αναζήτησης ή σύγκλισης του GWO.
    # Υπολογισμός της παραμέτρου C που σχετίζεται με την σύγκλιση σε υποψήφια λύση.
    C = 2 * r2
    
    #Υπολογισμός της απόστασης D μεταξύ του τρέχοντα λύκου και των τριών καλύτερων λύκων. 
    # D = |C * x_best_wolf[v][0][problems_variables] - x_current_wolf|
    D_alpha = abs(C * best_wolves_dictionary[0][0][dimension] - wolf_position)
    D_beta = abs(C * best_wolves_dictionary[1][0][dimension] - wolf_position)
    D_delta = abs(C * best_wolves_dictionary[2][0][dimension] - wolf_position)
    
    # Ενημέρωση του αντίστοιχου στοιχείου new_position_temp_vector με την υπολογισμένη τιμή.
    # Υπολογισμός της νέας συντεταγμένης της τρέχουσας διάστασης βάσει του τύπου X[dimension] = best_wolf_position - A * D.      
    position_on_current_dimension_based_on_alpha_wolf = best_wolves_dictionary[0][0][dimension] - A * D_alpha
    position_on_current_dimension_based_on_beta_wolf = best_wolves_dictionary[1][0][dimension] - A * D_beta
    position_on_current_dimension_based_on_delta_wolf = best_wolves_dictionary[2][0][dimension] - A * D_delta    
    new_position_on_current_dimension = (position_on_current_dimension_based_on_alpha_wolf + position_on_current_dimension_based_on_beta_wolf + position_on_current_dimension_based_on_delta_wolf) / 3
    #Επιστροφή της νέας θέση του τρέχοντος λύκου για την τρέχουσα διάσταση.
    return new_position_on_current_dimension

def GWO(wolves_number, max_iteration_num, min_fitness_standard_deviation, benchmark_function, plot_graph_enabled, gui_callback=None, stop_event=None):    
    """
    Η συνάρτηση υλοποιεί τον αλγόριθμο GWO για την εύρεση του ολικού βέλτιστου ενός δεδομένου προβλήματος.
    
    Αρχικά εκτελείται η αρχικοποίηση των θέσεων των πρακτόρων αναζήτησης (λύκων), εν συνεχεία σε επαναληπτικά βήματα προσαρμόζει συνεχώς
    τις θέσεις των λύκων με βάση ττις θέσεις των τριών ηγετών λύκων, μειώνει την παράμετρο a που ισοροπεί τις φάσεις της εξερεύνησης και της εκμετάλευσης
    της ευρεθείσας υποψήφιας λύσης. Τέλος Επιστρέφονται τα αποτελέσματα με την θέση του ανευρεθέντος βέλτιστου κ.α.

    Args:
        wolves_number (int): Το μέγεθος του πληθυσμού των λύκων.
        max_iteration_num (int): Ο μέγιστος αριθμός επαναλήψεων για τον αλγόριθμο (Κριτήριο Τερματισμού Α).
        min_fitness_standard_deviation (float): Η ελάχιστη τυπική απόκλιση των fitness για να σταματήσει η αναζήτηση (Κριτήριο Τερματισμού Β).
        benchmark_function (BenchmarkFunction): Η συνάρτηση benchmark για την οποία εκτελείται η βελτιστοποίηση.
        plot_graph_enabled (bool): Σημαία για την απεικόνιση της γραφικής παράστασης της διαδικασίας αναζήτησης.

    Returns:
        dict: Λεξικό με τα αποτελέσματα της εκτέλεσης του αλγορίθμου.
            Το λεξικό περιέχει τα εξής πεδία:
            - "global_minimum_value": Η τιμή του ολικού ελάχιστου της συνάρτησης benchmark.
            - "mean_fitness": Ο μέσος όρος της fitness των λύκων.
            - "min_fitness": Η ελάχιστη fitness από όλους τους λύκους.
            - "fitness_standard_deviation": Η τυπική απόκλιση των fitness.
            - "positional_deviation": Η ευκλείδια απόσταση της θέσης του άλφα λύκου από το ολικό ελάχιστο.
            - "iterations": Ο αριθμός των επαναλήψεων του αλγορίθμου.
            - "gwo_time": Ο χρόνος εκτέλεσης του αλγορίθμου σε δευτερόλεπτα.
    """    
    #Καταγραφή του χρόνου έναρξης της εκτέλεσης του αλγορίθμου.
    start = perf_counter()  
    
    if wolves_number < 3:
        if gui_callback:
            return {"error" : "At least 3 Wolves required (alpha, beta, delta.", "gwo_time" : 0}
        else:
            raise ValueError("At least 3 Wolves required (alpha, beta, delta.")
        
    lower_bound, upper_bound = benchmark_function.get_fbounds()
    variables_number = benchmark_function.dimensions
        
    # Δημιουργία ενός NumPy πίνακα διαστάσης wolves_number * variables_number ο οποίος περιέχει τις θέσεις των λύκων.  
    wolves_pos_array = np.random.uniform(low=lower_bound, high=upper_bound, size=(wolves_number, variables_number))
    # Αρχικοποίηση της παραμέτρου a που σχετίζεται με την ισορροπία μεταξύ των φάσεων εξερεύνησης και εκμετάλευσης.
    a_factor = 2
    # Μετρητής επαναλήψεων του αλγορίθμου.
    iteration_counter = 0

    # Κλήση της find_best_wolves() για την έυρεση των λύκων α,β,δ και επιστροφή τους μαζί με την απόκλιση του fitness όλων των λύκων.
    best_wolves_dictionary, fitness_standard_deviation, wolves_fitness_numpy_array = find_best_three_wolves(wolves_pos_array, benchmark_function, iteration_counter, plot_graph_enabled, gui_callback, stop_event)    
    
    # Εκτέλεση της Αναζήτησης για έναν συγκεκριμένο αριθμό επαναλήψεων (max_iteration_num) ή εως ότου η τυπική απόκλιση των καταλληλοτήτων των λύκων μειωθεί.
    # περισσότερο απο κάποιο κατώφλι (fitness_standart_deviation)
    while iteration_counter < max_iteration_num and fitness_standard_deviation > min_fitness_standard_deviation:

        if stop_event and stop_event.is_set():
            if gui_callback:
                gui_callback("log", f"GWO: forcing the algorithm to stop at iteration {iteration_counter} due to stop signal.")
            break

        # Σε κάθε επανάληψη του αλγορίθμου εκτελείται μία ανακύκλωση στον πληθυσμό των λύκων.
        for wolf in range(wolves_number):
            if stop_event and stop_event.is_set(): break

            # Για κάθε λύκο και για κάθε μεταβλητή (διάσταση).
            for every_dimension in range(variables_number):
                # καλείται η calculate_new_position() και υπολογίζεται η νέα θέση του λύκου με βάση τις θέσεις των λύκων ηγετών ως ο μέσος όρος αυτών.
                new_position = calculate_new_position(best_wolves_dictionary, wolves_pos_array[wolf, every_dimension], a_factor, every_dimension)
                # Επίσης για κάθε συντεταγμένη της νέας θέσης καλείται η np.clip() η οποία ελέγχει και αν χρειάζεται μεταφέρει εντός ορίων συνάρτησης την νέα θέση.
                wolves_pos_array[wolf, every_dimension] = np.clip(new_position,lower_bound,upper_bound)

        # Η παράμετρος α μειώνεται γραμμικά σύμφωνα με τον τύπο της θεωρίας σε κάθε επανάληψη(σταδιακή μετάβαση απο την εξερεύνηση στην εκμετάλλευση).
        a_factor = 2 - iteration_counter * (2 / max_iteration_num)
        # Υπολογισμός εκ νεόυ των τριών ηγετών λύκων.
        best_wolves_dictionary, fitness_standard_deviation, wolves_fitness_numpy_array = find_best_three_wolves(wolves_pos_array, benchmark_function, iteration_counter, plot_graph_enabled, gui_callback, stop_event)    
        
        if gui_callback:
            alpha_fitness_val = float('inf')

            if 0 in best_wolves_dictionary and best_wolves_dictionary[0] and len(best_wolves_dictionary[0]) > 1:
                alpha_fitness_val = best_wolves_dictionary[0][1]

            #Στέλνουμε στο GUI ενα λεξικό με τα δεδομενα για ενημέρωση των στοιχείων του GUI
            gui_callback("progress_update",{
                "iteration" : iteration_counter,
                "max_iterations": max_iteration_num,
                "alpha_fitness" : best_wolves_dictionary[0][1],
                "std_dev": fitness_standard_deviation,
                #"convergence_data": (iteration_counter, best_wolves_dictionary[0][1])                
            })
            #Σε περίπτωση προβλήματος με 2 μεταβλητές στέλνουμε και τα απαραίτητα δεδομένα πάλι σε λεξικό
            # για την σχεδίαση των γραφημάτων
            if benchmark_function.dimensions ==2 and plot_graph_enabled:
                #print(f"DEBUG GWO: Sending spatial_plot_data at itereration: {iteration_counter}")
                gui_callback("spatial_plot_data",{
                                            "iteration" : iteration_counter,
                                            "wolves_positions" : wolves_pos_array.copy(),
                                            "wolves_fitness" : wolves_fitness_numpy_array.copy(),
                                            #"beanchmark_function" : benchmark_function,                                                              
                                            })    
        # Αύξηση του μετρητή επαναλήψεων . 
        iteration_counter += 1

    end = perf_counter()
    gwo_time = end - start

    #Συντεταγμένες Ακριβούς Ολικού Ελαχίστου.
    global_minimum_point_coords = np.array(benchmark_function.get_fminimum_point())    
    #Συντεταγμένες σημείου της τρέχουσας ευρεθείσας λύσης (Συντεταγμένες Θέσης Λύκου Alpha)
    alpha_wolf_position = np.array(best_wolves_dictionary[0][0])
    # Υπολογισμός της απόκλισης από το ολικό ελάχιστο με υπολογισμό της ευκλείδιας απόστασης του άλφα λύκου απο το ολικό ελάχιστο.
    positional_deviation = np.linalg.norm(alpha_wolf_position - global_minimum_point_coords)

    if 0 in best_wolves_dictionary and best_wolves_dictionary[0]:
            if best_wolves_dictionary[0][0] is not None:
                alpha_wolf_position = np.array(best_wolves_dictionary[0][0])
            if best_wolves_dictionary[0][1] is not None:
                alpha_wolf_fitness_final = best_wolves_dictionary[0][1]
                
    positional_deviation = np.linalg.norm(alpha_wolf_position - global_minimum_point_coords) if not np.any(np.isnan(alpha_wolf_position)) else np.nan

        # Έλεγχος αν το array δεν είναι άδειο
    if len(wolves_fitness_numpy_array) > 0:
        # Επιλογή μόνο των πεπερασμένων τιμών (όχι NaN ή Inf)
        finite_values = wolves_fitness_numpy_array[np.isfinite(wolves_fitness_numpy_array)]

        # Έλεγχος αν υπάρχουν πεπερασμένες τιμές
        if len(finite_values) > 0:
            min_fitness_overall = np.min(finite_values)
            mean_fitness_overall = np.mean(finite_values)
        else:
            min_fitness_overall = np.inf
            mean_fitness_overall = np.inf
    else:
        min_fitness_overall = np.inf
        mean_fitness_overall = np.inf

    if fitness_standard_deviation is None:
        fitness_std = np.inf
    else:
        fitness_std = fitness_standard_deviation

    # Δημιουργία λεξικού με τα αποτελέσματα.
    results = {
        "global_minimum_value": benchmark_function.get_fminimum_value(),               
        "mean_fitness": mean_fitness_overall,        
        "min_fitness": min_fitness_overall, # Η συνολική καλύτερη fitness που βρέθηκε
        "alpha_wolf_fitness": alpha_wolf_fitness_final, # Η fitness του alpha στο τέλος
        "alpha_wolf_position": alpha_wolf_position.tolist(), # Μετατροπή σε λίστα
        "fitness_standard_deviation" : fitness_std,
        "positional_deviation": positional_deviation,       
        "iterations": iteration_counter, # Ο αριθμός των επαναλήψεων που ολοκληρώθηκαν
        "gwo_time": gwo_time
    }
    
    #Επιστροφή του λεξικού των αποτελεσμάτων.
    return results