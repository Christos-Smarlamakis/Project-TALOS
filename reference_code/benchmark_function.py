# -*- coding: utf-8 -*-
"""
@Student: Christos Smarlamakis
std147661@ac.eap.gr, christossmarlamakis@gmail.com / 6945830515
"""

import numpy as np

class BenchmarkFunction:
    
    """
    Η κλάση αυτή δημιουργεί αντικείμενα συναρτήσεων benchmark (δοκιμής).    
    """
    
    def __init__(self, name, dimensions=2):
        """
            Αρχικοποιητής με ορισμα το όνομα της συνάρτησης δοκιμής     
        """
        self.name = name #Πεδίο για το όνομα της συνάρτησης
        self.dimensions = dimensions #Πεδίο για το πλήθος των μεταβλητών του προβλήματος / διαστάσεις προβλήματος
        self.lower_bound, self.upper_bound = self.get_fbounds() #πεδία για τα όρια της συνάρτησης

    def get_name(self):
        """
            Η get_name(self) επιστρέφει το όνομα της συνάρτησης αξιολόγησης.
        """
        return self.name.capitalize()
        

    def get_fbounds(self):
        """
        Η get_bounds() επιστρέφει τα όρια της τρέχουσας συνάρτησης δοκιμής.
        """
        if self.name == "ackley": #F10
            return -32, +32
        elif self.name == "rastrigin": #F9
            return -5.12, +5.12
        elif self.name == "rosenbrock": #F5
            return -30, +30
        elif self.name == "sphere": #F1
            return -100 ,+100
        elif self.name == "griewank": #F11
            return -600, +600
        elif self.name == "dejongF5_foxholes": #F14
            return -65.536, +65.536
        elif self.name == "goldstein-price": #F18
            return -2, +2
        else:
            raise ValueError("Unknown benchmark function")
    
    def get_fminimum_value(self):
        """
        Η get_actual_minimum() επιστρέφει το πραγματικό ελάχιστο της τρέχουσας συνάρτησης δοκιμής
        """
        if self.name == "ackley":
            return 0  
        elif self.name == "griewank":
            return 0  
        elif self.name == "rastrigin":
            return 0  
        elif self.name == "rosenbrock":
            return 0  
        elif self.name == "sphere":
            return 0
        elif self.name == "dejongF5_foxholes":
            return 1
        elif self.name =="goldstein-price":
            return 3
        else:
            raise ValueError("Unknown benchmark function")
            
    def get_fminimum_point(self):
        """
        Η get_actual_minimum() επιστρέφει το πραγματικό ελάχιστο της τρέχουσας συνάρτησης δοκιμής
        """
        if self.name == "ackley":
            return tuple(0 for _ in range(self.dimensions))  #(0,...0)
        elif self.name == "griewank":
            return tuple(0 for _ in range(self.dimensions))  #(0,...0)
        elif self.name == "rastrigin":
            return tuple(0 for _ in range(self.dimensions))  #(0,...0)  
        elif self.name == "rosenbrock":
            return tuple(1 for _ in range(self.dimensions))  #(1,...0)  
        elif self.name == "sphere":
            return tuple(0 for _ in range(self.dimensions))  #(0,...0) 
        elif self.name == "dejongF5_foxholes":
            return tuple(-32 for _ in range(2))                #(-32,-32)
        elif self.name == "goldstein-price":
            return (0, -1)                                   #(0,-1)
        else:
            raise ValueError("Unknown benchmark function")     
                       
    def calculate_fitness(self, x):
        
        """
        Η συνάρτηση calculate_fitness() παίρνει ως όρισμα μία λίστα/πίνακα με τις συντεταγμένες της θέσης
        και υπολογίζει την καταλληλότητα του λύκου (πράκτορα αναζήτησης)
        """
        n = len(x)
        if self.name == "ackley": #F10 - Multimodal Function
            # f(x) = -20⋅exp(-0.2⋅√(1/n ⋅ Σᵢ (xᵢ²))) - exp(1/n ⋅ Σᵢ (cos(2π⋅xᵢ))) + 20 + e
            x = np.array(x)
            sum_term = np.sum(x**2) / n
            cos_term = np.sum(np.cos(2 * np.pi * x)) / n            
            return -20 * np.exp(-0.2 * np.sqrt(sum_term)) - np.exp(cos_term) + 20 + np.e
           
        elif self.name == "griewank": #F11 - Multimodal Function
            # f(x) = 1 + 1/4000⋅Σᵢ (xᵢ²) - Πᵢ (cos(xᵢ/√i))
            x = np.array(x)
            sum_term = np.sum(x**2) / 4000
            prod_term = np.prod(np.cos(x / np.sqrt(np.arange(1, n + 1))))            
            return 1 + sum_term - prod_term
        
        elif self.name == "rastrigin": #F9 - Multimodal Function
            # f(x) = 10n + Σᵢ (xᵢ² - 10⋅cos(2π⋅xᵢ))
            x = np.array(x)            
            return 10 * n + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))
        
        elif self.name == "rosenbrock":#F5 - Unimodal Function 
            # f(x) = Σᵢ (100(xᵢ₊₁ - xᵢ²)² + (xᵢ - 1)²)
            x = np.array(x)
            return np.sum(100 * (x[1:n] - (x[0 : n - 1] ** 2)) ** 2 + (x[0 : n - 1] - 1) ** 2)
        
        elif self.name =="sphere": #F1 - Unimodal Function
            # f(x) = ∑ᵢ (xᵢ²)
            x = np.array(x)            
            return np.sum(x**2)
        
        elif self.name =="dejongF5_foxholes": #F14 - Fixed Dimension Multimodal Function dimensions=2
            # f(x) = 1 / (0.002 + Σ(i=1, 25) [1 / (i + (x₁ - A₁ᵢ)⁶ + (x₂ - A₂ᵢ)⁶)])
            x1, x2 = x[0], x[1]
            A = np.zeros((2, 25))
            a = np.array([-32, -16, 0, 16, 32])
            A[0, :] = np.tile(a, 5)
            A[1, :] = np.repeat(a, 5)

            sumterm1 = np.arange(1, 26)
            sumterm2 = (x1 - A[0, :]) ** 6
            sumterm3 = (x2 - A[1, :]) ** 6
            
            sum_terms = np.sum(1 / (sumterm1 + sumterm2 + sumterm3))            
            return 1 / (0.002 + sum_terms)
        
        elif self.name =="goldstein-price": #F18 - Fixed Dimension Multimodal Function dimensions=2
            #f(x₁, x₂) = (1 + ((x₁ + x₂ + 1)²)(19 - 14x₁ + 3x₁² - 14x₂ + 6x₁x₂ + 3x₂²)) 
            #            × (30 + ((2x₁ - 3x₂)²)(18 - 32x₁ + 12x₁² + 48x₂ - 36x₁x₂ + 27x₂²))
            x = np.array(x)
            x1 = x[0]
            x2 = x[1]           
            subterm1a = (x1 + x2 + 1)**2
            subterm1b = 19 - 14*x1 + 3*x1**2 - 14*x2 + 6*x1*x2 + 3*x2**2
            
            term1 = 1 + subterm1a * subterm1b         
            subterm2a = (2*x1 - 3*x2)**2
            subterm2b = 18 - 32*x1 + 12*x1**2 + 48*x2 - 36*x1*x2 + 27*x2**2
            
            term2 = 30 + subterm2a * subterm2b           
            return term1 * term2        
        else:
            raise ValueError("Unknown benchmark function") 