import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

import threading
import queue
import os
import csv

from benchmark_function import BenchmarkFunction
from gwo import GWO

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np


class GWOApp(tb.Window):

    # 1. Αρχικοποιητής =================================================================================================

    def __init__(self):
        #Αρχικοποίηση του παραθύρου με το θέμα darkly του ttkbootstrap
        super().__init__()
        # Δηλώνουμε ενα λεξικό που θα αποθηκεύονται τα δεδομένα εισόδου του χρήστη.       
        self.parameters_dict = {}
        #Λίστα με όλα τα διαθέσιμα θέματα του ttkbootstrap
        #self.themes = 
        #[
        #    "superhero", "litera", "cosmo", "flatly", "journal", "lumen", 
        #    "minty", "pulse", "sandstone", "united", "yeti", "cyborg", 
        #    "darkly", "solar", "vapor"
        #]
        self.themes = ["minty", "cosmo","sandstone", "united", "yeti", "superhero", "solar", "vapor", "cyborg"]
        self.dark_ttk_themes = ["superhero", "solar", "vapor", "cyborg"]
        # Το αρχικό Θέμα της εφαρμογής μας
        initial_theme = "cyborg"        
        # Αρχικά Θέτουμε το background των γραφημάτων να ειναι Σκουρόχρωμο
        self.plot_dark_background_var = tk.BooleanVar(value = True)
        # Καλούμε την private μέθοδο για αρχικοποίηση των χρωμάτων φόντου των γραφημάτων.
        self._update_plot_bg_colors()

        self.plot_update_counter = 0        
        self.style.theme_use(initial_theme)       
        
        # --- Μεταβλητές για τα control Buttons των γραφημάτων --- 
        # Μεταβλητή για το Toggle Button του γραφήματος Σύγκλισης Καταλληλότητας.
        self.enable_convergence_plot_var = tk.BooleanVar(value=True)
        # Για τα RadioButtons (3d_view και top_view)
        self.active_spatial_plot_var = tk.StringVar(value="3d_view")
        # Ενεργοποίηση της ενημέρωσης των γραφημάτων του χώρου αναζήτησης και των πρακτόρων (λύκων). 
        self.enable_spatial_live_update_var = tk.BooleanVar(value=True)        

        self.title("GWO Algorithm Simulator")
        self.geometry("1350x850")

        self.benchmark_functions_name_list = ["ackley", "griewank", "rastrigin", "rosenbrock","sphere","dejongF5_foxholes","goldstein-price"]
        self.fixed_dim_functions =["dejongF5_foxholes","goldstein-price"]

        # --- Μεταβλητές για την πολυνηματική επεξεργασία και την επικοινωνία μεταξύ του νήματος του GUI και του GWO ---
        self.gwo_thread = None # Νήμα εκτέλεσης GWO
        self.stop_event = threading.Event() # Event για την διακοπή εκτέλεσης του νήματος
        self.gui_queue = queue.Queue() # Thread Safe δομή (ουρα) για την αποστολή μνμ απο το νήμα του GWO στο νήμα του GUI
        self.parameters_dict = {} # Λεξικό για την αποθήκευση των τιμών των παραμέτρων απο τα πεδία εισόδου του GUI
        
        # --- Μεταβλητές και Ρυθμίσεις Γραφημάτων ---
        # Λεξικό για την αποθήκευση των στοιχείων της κάθε καρτέλας (fig, ax, canvas)
        self.plot_tabs_dict = {} 
        self.plot_configs_list = [
            {"key" : "3d_view", "title" : "3D View", "projection" : "3d"},
            {"key" : "top_view", "title" : "Top View", "projection" : None},
            {"key" : "convergence", "title" : "Convergence Curve", "projection" : None}
        ]
        self.convergence_data = {"iterations" : [], "fitness" : []}

        # Το τρέχον αντικείμενο benchmark για το οποίο έχει σχεδιαστεί η συνάρτηση αξιολόγησης
        self.current_benchmark_object_for_spatial_plot = None 
        # Μεταβλητή για να κρατάμε το αντικείμενο της γραφικης παράστασης 3D View
        self.plotted_3d_surface = None
        # Ομοίως για την γραφική παράσταση top_view
        self.plotted_top_view_contour = None
        # Βοηθητική μεταβλητή για το colorbar της Top View
        self.plotted_top_view_colorbar = None
        # Βοητική μεταβλητή γιο τις θέσεις των Λύκων στο 3D Διάγραμμα
        self.scatter_3d_wolves = None
        # Βοηθητική Μεταβλητή για τις θέσεις των Λύκων στο Top View
        self.scatter_top_view_wolves = None
        # Μεταβλητή για την άθροιση του χρόνου εκτέλεσης σε κάθε RUN
        self.cumulative_execution_time = 0.0

        # Καλούμε την μέθοδο create_widgets() για την σχεδίαση των widgets στο GUI.
        self.create_widgets()
        # Εκτέλεση της process_gui_queue() κάθε 100ms για έλεγχο μνμ εισερχόμενων απο το νήμα του GWO
        self.after(100, self.process_gui_queue)       

        # Παρεμβαίνουμε στο κλείσιμο της εφαρμογής απο το ΛΣ όταν ο χρήστης πατάει το 'Χ' του παραθύρου, 
        # εκτελώντας την δική μας συνάρτηση on_closing()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)    

    # 2. Μέθοδοι Δημιουργίας Κύριων Τμημάτων του GUI (Layout) ==========================================================

    def create_widgets(self):
        """
            Η μέθοδος δημιουργεί όλα τα κύρια widgets (Frames, Input fields, Labels, Buttons, Plots) και τα 
            τοποθετεί μέσα στο κύριο παράθυρο της εφαρμογής. 
            Δημιουργουνται: 
            1 πλαίσιο για το combobox Και το toggle button για την επιλογή Σκούρου Θέματος και Φόντου
            Γραφημάτων, 
            1 panedWindow που χωρίζει το παράθυρο σε δεξί και αριστερό μέρος, 
            1 left pane που περιέχει τα πεδία εισόδου των παραμέτρων και τα toggle buttons και spinbox για
            τον έλεγχο της εμφάνισης των γραφημάτων καθώς και κουμπιά έναρξης και παύσης του αλγορίθμου.            
            1 right pane που περιέχει ενα Notebook με καρτέλες για καθε γραφική παράσταση.
        """
        # Δημιουργούμε ένα πλαίσιο container που θα μπει στην κορυφή του κυρίως παραθύρου.
        top_frame = tb.Frame(self, padding=(10, 10, 10, 0))
        # Το τοποθετούμε στο κυρίως παράθυρο, στο πάνω μέρος και καταλαμβάνει 
        # όλο το μήκος του παραθύρου (fill=X).
        top_frame.pack(fill=X, side=TOP)
        # Δημιουργούνται τα widget για την επιλογή του θέματος και του φόντου γραφήματος
        self.create_theme_chooser_frame(top_frame)        

        # Δημιουργία ενος αντικειμένου PanedWindow() στο κυρίως παράθυρο της εφαρμογής
        # που το χωρίζει σε δύο κάθετα τμήματα αριστερό και δεξί μεταβλητού μήκους.
        main_paned_window = ttk.PanedWindow(self, orient=HORIZONTAL)
        # Το τοποθετούμε στο παράθυρο και το ρυθμίζουμε για πλήρη κάλυψη της περιοχής, αυτόματη προσαρμογή στο παράθυρο.
        main_paned_window.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Δημιουργούμε ένα Frame για την ομαδοποίηση widgets.
        left_frame = tb.Frame(main_paned_window, padding=10)
        # Το τοποθετούμε μέσα στο paned window.
        main_paned_window.add(left_frame)

        # Ομοίως δημιουργούμε ένα ακόμα Frame και το τοποθετούμε και αυτό στο δεξί panedWindow.
        right_frame = tb.Frame(main_paned_window, padding=10)
        main_paned_window.add(right_frame)

       # --- Καλούμε μεθόδους για την δημιουργία των περιεχομένων των Frames
        # Δημιουργία των πεδίων εισόδου των παραμέτρων του αλγορίθμου.
        self.create_parameters_frame(left_frame)
        # Δημιουργία των toggle buttons για την εμφάνιση των γραφημάτων και των Control Buttons (START-STOP)
        self.create_plot_control_options_frame(left_frame)
        # Εμφάνιση της μπάρας προόδου της διαδικασίας βελτιστοποίσης
        self.create_progress_frame(left_frame)
        # Δημιουργία του Frame για την εμφάνιση μυνημάτων στον Χρήστη.
        self.create_log_frame(left_frame)
        # Δημιουργία του Notebook στο δεξί μέρος του παραθύρου με τις 
        # καρτέλες των γραφημάτων.
        self.create_plots_frame(right_frame)
        # Εφαρμογή των χρωμάτων του επιλεχθέντος θέματος στα γραφήματα
        # για καλύτερο UI/UX.
        self.on_theme_select(update_plots=True)


    def create_theme_chooser_frame(self, parent):
        """
            Δημιουργούμε ενα πλαίσιο και τοποθετούμε ενα Label και ενα combobox
            για την επιλογή ενός θέματος απο τα διαθέσιμα της λίστας.

            Args:
            parent (tk.widget): Περνιέται ως παράμετρος το γονικό widget μέσα στο 
            οποίο θα δημιουργηθεί  το LabelFrame των widgets για το Log Frame.
        """
        # Δημιουργούμε ενα εξωτερικό πλαίσιο για τα δύο widgets επιλογης θέματος 
        # και χρώματος φόντου γραφημάτων.
        theme_outer_frame = tb.Frame(parent)
        # Τοποθετουμε το Frame στην δεξιά πλευρά του γονικού παραθύρου 
        # για να είναι ευδιάκριτα απο τον Χρήστη
        theme_outer_frame.pack(side=RIGHT, fill=X, padx=5)

        # Δημιουργούμε το Frame που θα φιλοξενήσει το dropbox επιλογής θέματος 
        # και το αγκιστρώνουμε στο εξωτερικό Frame
        theme_select_frame = tb.Frame(theme_outer_frame)
        theme_select_frame.pack(side=LEFT, padx=(0,10))
        tb.Label(theme_select_frame, text="App Theme:").pack(side=LEFT, padx=(0,5))

        # Δημιουργία του Combobox για την επιλογή θέματος.
        self.theme_combo = ttk.Combobox(theme_select_frame, 
                                        values=self.themes, 
                                        state="readonly", 
                                        width=15)
        self.theme_combo.pack(side=LEFT)
        # Ορίζει την αρχική επιλεγμένη τιμή του combobox να είναι το ενεργό τρέχον θέμα
        self.theme_combo.set(self.style.theme.name)
        # Οταν ο χρήστης κανει μια επιλογή απο το combobox καλείται η μέθοδος on_theme_select().
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_select)

        # Δημιουργούμε ακόμη ένα εσωτερικό Frame που θα βάλουμε ένα checkbox για
        # την επιλογή σκουρόχρωμου φόντου στα γραφήματα
        plot_style_frame = tb.Frame(theme_outer_frame)
        plot_style_frame.pack(side=LEFT)
        self.plot_bg_check = tb.Checkbutton(
            plot_style_frame,
            text = "Dark Plot Background",
            variable = self.plot_dark_background_var,
            bootstyle = "primary-round-toggle",
            command = self.on_plot_background_toggle
        )
        self.plot_bg_check.pack(side=LEFT, padx=5) 

    def create_parameters_frame(self, parent):
        """
            Δημιουργούμε ενα πλαίσιο για να ομαδοποιήσουμε τα widgets πεδίων εισόδου των παραμέτρων

            Args:
            parent (tk.widget): Περνιέται ως παράμετρος το γονικό widget μέσα στο οποίο θα δημιουργηθεί
            το LabelFrame των παραμέτρων.
        """
        # Δημιουργούμε ενα LabelFrame, ενα πλαίσιο με ετικέτα για την φιλοξενία.
        parameters_frame = tb.LabelFrame(parent, text="Parameters", padding=10, bootstyle=PRIMARY)       
        # Τοποθετούμε το Frame στο γονικό widget που ειναι το left_frame το οποίο και θα πιάσει όλο το 
        # πλάτος του left_frame (fill=X), pady=(0,10) σημαίνει εωτερικό κενό πάνω 0 και κάτω 10.
        parameters_frame.pack(fill=X, pady=(0,10))        

        # --- Widget 1: Επιλογή Συνάρτησης (Combobox).
        tb.Label(parameters_frame, text="Benchmark Function: ").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        # Αποθηκεύουμε στο ζεύγος του λεξικού με key=benchmark την τιμη μίας μεταβλητή τύπου StringVar 
        # η οποία ακούει για τυχόν αλλαγές.
        self.parameters_dict["benchmark"] = tk.StringVar()
        
        # Δημιουργούμε ενα comboBox για να επιλέγει ο χρήστης συνάρτηση αξιολόγησης απο μία λίστα
        # και να αποθηκεύεται στην μεταβλητη StringVar και άρα στο ζεύγος του λεξικού με key=benchmark.
        self.benchmark_combobox = ttk.Combobox(
            parameters_frame, # Τοποθετούμε το combobox στο Frame των παραμέτρων
            textvariable=self.parameters_dict["benchmark"], # Συνδέουμε το widget με την μεταβλητή self.parameters_dict["benchmark"]
            values=self.benchmark_functions_name_list, # Περνάμε ώς όρισμα το πεδίο της κλάσης που είναι μία λίστα συναρτήσεν αξιολόγησης
            state="readonly", # Δεν μπορεί ο Χρήστης να γράψει στο combobox
            width=25
        )
        # Προσθέτουμε ενα PlaceHolder
        self.benchmark_combobox.set("Select a function...")
        # Τοποθετουμε το combobox στο πλέγμα στην γραμμή 0, στήλη 1 και κολλάει απο την Ανατολική Πλευρά μέχρι την Δυτική (EAST-WEST=EW).
        self.benchmark_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
        # Με την κάτωθι εντολή δημιουργούμε εναν event listener στο combobox.
        self.benchmark_combobox.bind("<<ComboboxSelected>>", self.on_benchmark_select)

        # --- Widget 2: Πεδίο Κειμένου για τις Διαστάσεις
        tb.Label(parameters_frame, text="Dimensions:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        # Η μεταβλητή StringVar() συνδέεται με το widget και ακουεί για τιμές εισόδου απο τον Χρήστη
        self.parameters_dict["dimensions"] = tk.StringVar(value="2")
        # Δημιουργούμε το Πεδίο Εισόδου και το συνδέουμε με την μεταβλητή self.parameters_dict["dimensions"]
        self.dimensions_entry = tb.Entry(parameters_frame, textvariable=self.parameters_dict["dimensions"],state="disabled", width=28)
        self.dimensions_entry.grid(row=1, column=1, padx=5, pady=5, sticky=EW)
        
        # --- Widget 3: Πεδίου Κειμένου για το πλήθος των Λύκων
        tb.Label(parameters_frame, text="Wolves Number:").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        self.parameters_dict["wolves"] = tk.StringVar(value="30")
        #Ομοίως πεδίο εισόδου για την επιλογή πρακτόρων αναζήτησης, σύνδεση με μεταβλητή self.parameters_dict["wolves"]
        self.wolves_entry = tb.Entry(parameters_frame, textvariable=self.parameters_dict["wolves"], width=28)
        self.wolves_entry.grid(row=2, column=1, padx=5, pady=5, sticky=EW)

        # --- Widget 4: Μέγιστο Πλήθος Επαναλήψεων Αλγορίθμου
        tb.Label(parameters_frame, text="Max Iterations:").grid(row=3, column=0, padx=5, pady=5, sticky=W)
        self.parameters_dict["max_iter"] = tk.StringVar(value="100")
        self.max_iter_entry = tb.Entry(parameters_frame, textvariable=self.parameters_dict["max_iter"], width=28)
        self.max_iter_entry.grid(row=3, column=1, padx=5, pady=5, sticky=EW)

        # --- Widget 5: Ελάχιστη Τυπική Απόκλιση
        tb.Label(parameters_frame, text="Min Fitness Std Dev:").grid(row=4, column=0, padx=5, pady=5, sticky=W)
        self.parameters_dict["min_std_dev"] = tk.StringVar(value="1e-10")
        self.min_std_dev_entry = tb.Entry(parameters_frame, textvariable=self.parameters_dict["min_std_dev"], width=28)
        self.min_std_dev_entry.grid(row=4, column=1, padx=5, pady=5, sticky=EW)

        # --- Widget 6: Αριθμός Εκτελέσεων
        tb.Label(parameters_frame, text="Number of Runs:").grid(row=5, column=0, padx=5, pady=5, sticky=tb.W)
        self.parameters_dict["runs"] = tk.StringVar(value="1")
        self.runs_entry = tb.Entry(parameters_frame, textvariable=self.parameters_dict["runs"], width=28)
        self.runs_entry.grid(row=5, column=1, padx=5, pady=5, sticky=EW)      

       
    def create_plot_control_options_frame(self, parent):

        """
            Η Συνάρτηση δημιουργεί ένα LabelFrame που περιέχει τα στοιχεία ελέγχου
            για τις επιλογές εμφάνισης των γραφημάτων (Ενεργοποίηση Καμπύλης Σύγκλισης - Χωρικών Γραφημάτων)
            καθώς και τα κουμπιά έναρξης και πάυσης της εκτέλεσης του GWO (RUN-STOP)

            Args:
            parent (tk.widget): Περνιέται ως παράμετρος το γονικό widget μέσα στο οποίο θα δημιουργηθεί
            το LabelFrame των Control Widgets.
        """

        # Δημιουργούμε το LabelFrame και το τοποθετούμε.
        plot_controls_lf = tb.LabelFrame(parent, text="Plot's Controls", padding=10, bootstyle=WARNING) 
        plot_controls_lf.pack(fill=X, pady=(0, 10))

        # --- Widget 1: Toggle για Εμφάνιση Καμπύλης Σύγκλισης Καταλληλότητας (Convergence Curve).
        self.conv_live_update_check = tb.Checkbutton(
            plot_controls_lf, # Γονικό LabelFrame
            text="Draw Convergence Curve", # Το Κείμενο του Label
            variable=self.enable_convergence_plot_var, # Σύνδεση με την Boolean self.enable_convergence_plot_var
            bootstyle="info-round-toggle" # Στύλ Κουμπιού
        )
        self.conv_live_update_check.grid(row=0, column=0, padx=5, pady=2, sticky=W)   

        # --- Widget 2: Toggle για τα Spatial Plots (3D/Top View) ---
        self.spatial_live_update_check = tb.Checkbutton(
            plot_controls_lf, # Γονέας το LabelFrame
            text="Draw Spatial Plots (Only the Active Tab)",
            variable=self.enable_spatial_live_update_var,
            bootstyle="info-round-toggle"
        )
        self.spatial_live_update_check.grid(row=1, column=0, padx=5, pady=2, sticky=W)

        # --- Widget 3: Spinbox για Επιλογή Συχνότητας Ενημέρωσης των Γραφημάτων ---
        # Δημιουργούμε ενα Label για την Εμφάνιση Κειμένου σχετικού με την λειτουργικότητα του SpinBox
        freq_label = tb.Label(plot_controls_lf, text="Plot's Update Frequency (plot/iterations):") 
        freq_label.grid(row=2, column=0, padx=5, pady=5, sticky=W)        
        # Δημιουργία ανώνυμης μεταβλητής StringVar με αρχική τιμή 5 που ακουεί τις επιλογές του χρήστη στο spinbox
        # και η τιμή καταχωρείται στο parameters_dict["plot_update_freq"]
        self.parameters_dict["plot_update_freq"] = tk.StringVar(value="5") 
        self.plot_update_freq_spinbox = ttk.Spinbox( # Άλλαξε το Entry σε Spinbox
            plot_controls_lf, # Γονικό widget
            from_=1, #  Σημείο Έναρξης
            to=100, # Λήξη
            increment=5, # Βήμα 
            textvariable=self.parameters_dict["plot_update_freq"], # Σύνδεση με Μεταβλητή Listener
            width=5, # πλάτος Spinbox
            state="readonly" # Ο χρήστης δεν μπορεί να εισάγει τιμές (ενδεχομένως Invalid).
        )
        self.plot_update_freq_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=W)

        # Δημιουργούμε ενα Frame για να ομαδοποιήσουμε τα κουμπιά
        control_frame = tb.Frame(parent)
        control_frame.pack(fill=X, pady=5)
    
        # Δημιουργούμε το κουμπί Run για την εκτέλεση του Αλγορίθμου και μόλις πατιέται καλείται η συνάρτηση start_gwo_thread_wrapper()
        self.run_button = tb.Button(control_frame,
                                    text="Run Algorithm", 
                                    command=self.start_gwo_thread_wrapper, 
                                    bootstyle=SUCCESS, 
                                    width=15)
        # Το τοποθετούμε στο αριστερό μέρος του control_frame
        self.run_button.pack(side=LEFT, padx=(0,5), expand=True, fill=X)

        # Δημιουργούμε κουμπί Stop Algorithm σε περίπτωση που θέλει ο χρήστης να τερματίσει πρόωρα την εκτέλεση του αλγορίθμου
        self.stop_button = tb.Button(control_frame,
                                     text="Stop Algorithm", 
                                     command=self.stop_gwo, 
                                     bootstyle=DANGER, 
                                     state=DISABLED,
                                     width=15)
        # Το τοποθετούμε δίπλα και δεξιά του Run Button
        self.stop_button.pack(side=LEFT, padx=5, expand=True, fill=X)

    def create_progress_frame(self, parent):
        """
            Δημιουργούμε ενα Frame που έχει ολα τα πεδία με τις ετικέτες για τα αποτελέσματα 
            του αλγορίθμου σε κάθε επανάληψη.

            Args:
            parent (tk.widget): Περνιέται ως παράμετρος το γονικό widget μέσα στο οποίο θα δημιουργηθεί
            το LabelFrame των σχετικών με την πρόοδο του αλγορίθμου widgets.
        """
        progress_frame = tb.LabelFrame(parent, text="Progress", padding=10,bootstyle=INFO)
        progress_frame.pack(fill=X,pady=10)

        # Δημιουγούμε τα Labels για τα αποτελέσματα
        # --- 1. "Current Run" ---
        tb.Label(progress_frame, text="Current Run:").grid(row=0, column=0,sticky=W, padx=5, pady=2)
        self.current_run_label = tb.Label(progress_frame, text="N/A", width=20)
        self.current_run_label.grid(row=0, column=1, sticky=W, padx=5, pady=2)

        # --- 2. "Current Iteration" ---
        tb.Label(progress_frame, text="Current Iteration:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.current_iter_label = tb.Label(progress_frame, text="N/A", width=20)
        self.current_iter_label.grid(row=1, column=1, sticky=W, padx=5, pady=2)

        # --- 3. "Best Fitness" ---
        tb.Label(progress_frame, text="Best Fitness:").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.alpha_fitness_label = tb.Label(progress_frame, text="N/A", width=20)
        self.alpha_fitness_label.grid(row=2, column=1, sticky=W, padx=5, pady=2)

        # --- 4. "Fitness Std Deviation" ---
        tb.Label(progress_frame, text="Fitness Std Deviation:").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        self.std_dev_label = tb.Label(progress_frame, text="N/A", width=20)
        self.std_dev_label.grid(row=3, column=1, sticky=W, padx=5, pady=2)

        # --- 5. "Execution Time" ---
        tb.Label(progress_frame, text="Execution Time (sec):").grid(row=4, column=0, sticky=W, padx=5, pady=2)
        self.exec_time_label = tb.Label(progress_frame, text="N/A", width=20)
        self.exec_time_label.grid(row=4, column=1, sticky=W, padx=5, pady=2)

        ttk.Separator(progress_frame, orient=HORIZONTAL).grid(row=5, column=0, columnspan=2, sticky=EW, pady=5)

        # Δημιουργούμε τη μπάρα προόδου.       
        self.progress_bar = tb.Progressbar(
            progress_frame, 
            orient=HORIZONTAL, 
            mode='determinate', 
            bootstyle=SUCCESS + STRIPED #πράσινο χρώμα με ρίγες.
        )
        self.progress_bar.grid(row=6, column=0, columnspan=2, sticky=EW, pady=(10,5))
   
    def create_log_frame(self, parent):
        """
            Δημιουργούμε ενα Frame και τοποθετούμε ενα Text widget  για την εμφάνιση πληροφοριων 
            σχετικών με την εκτέλεση του αλγορίθμου όπως σε ποιο Run είμαστε και που αποθηκεύθηκε 
            το αρχείο αποτελεσμάτων.

            Args:
            parent (tk.widget): Περνιέται ως παράμετρος το γονικό widget μέσα στο οποίο θα δημιουργηθεί
            το LabelFrame των widgets για το Log Frame.
        """      
        log_frame = tb.LabelFrame(parent, text="Log", padding=10, bootstyle=SECONDARY)        
        log_frame.pack(fill=BOTH, expand=True, pady=10)

        #Δημιουργούμε ένα Text widget για την εμφάνιση πληροφοριακών μυνημάτων στον Χρήστη.       
        self.log_text = tk.Text(log_frame, height=10, wrap=WORD, state=DISABLED)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        #Δημιουργούμε μια μπάρα κύλισης (Scrollbar).
        scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Συνδέουμε το Text widget με το scrollbar.
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _update_plot_bg_colors(self):
        """
            private συνάρτηση  που ενημερώνει τις μεταβλητές χρώματος φόντου των γραφημάτων 
            (self.plot_fig_gb_color, self.plot_axes_bg_color) με βάση την τίμη της 
            self.plot_dark_background_var.
        """
        # Αν ο χρήστης ενεργοποιήσει το toggle για σκούρο φόντο στα γραφήματα
        # Χρησιμοποιούμε hard coded χρώματα συμβατά και φιλικά στο χρήστη για μία
        # κατα το δυνατόν καλύτερη UX ειδικά όταν γίνεται χρήση dark θέματος για το gui
        if self.plot_dark_background_var.get():
            self.plot_fig_bg_color = '#2B3E50' 
            self.plot_axes_bg_color = '#34495E' 
        else: # Αλλιώς χρησιμοποιούμε το default λευκό
            self.plot_fig_bg_color = 'white'
            self.plot_axes_bg_color = 'white'     
    
    #3. Μέθοδοι Δημιουργίας και Αρχικοποίησης Γραφημάτων ===============================================================
    
    def create_plots_frame(self, parent):
        """
            Η μέθοδος δημιουργεί το πλαίσιο που περιέχει τα γραφήματα της εφαρμογής
            οργανωμένα σε καρτέλες χρησιμοποιώντας το widget ttk.Notebook.

            Args:
            parent (tk.widget): Περνιέται ως παράμετρος το γονικό widget μέσα στο 
            οποίο θα δημιουργηθεί το Notebook το οποίο είναι το right_frame.
            
        """

        # --- Δημιουργούμε το Notebook widget για να έχουμε καρτέλες.        
        self.plot_notebook = ttk.Notebook(parent, bootstyle="primary")
        self.plot_notebook.pack(fill=BOTH, expand=True, pady=(0, 5)) # Λίγο κενό κάτω

        # Δημιουργούμε ένα λεξικό για να αποθηκεύουμε τα στοιχεία κάθε καρτέλας (figure, axes, canvas)                
        self.plot_tabs_dict = {}        
        # Διατρέχουμε την λίστα με τα λεξικά των ρυθμίσεων κάθε καρτέλας γραφήματος
        for config in self.plot_configs_list:
            #Αποθηκεύομε σε κατάλληλες μεταβλητές τα values των αντίστοιχων keys
            key = config["key"]
            title = config["title"]
            projection = config["projection"]

            # Δημιουργούμε ένα Frame για να μπει ως καρτέλα του Notebook
            tab_frame = tb.Frame(self.plot_notebook, padding=5)
            self.plot_notebook.add(tab_frame, text=title) # Προσθέτουμε το frame ως νέα καρτέλα

            # Δημιουργούμε μια Matplotlib Figure που θα περιέχει όλα τα στοιχεία του γραφήματος            
            fig = plt.Figure(figsize=(6, 5), dpi=100) 

            # Προσθέτουμε Άξονες (Axes) στη Figure
            if projection == "3d":
                ax = fig.add_subplot(111, projection='3d') # πλέγμα 1x1, 3d απεικόνιση
            else:
                ax = fig.add_subplot(111) # πλέγμα 1x1, 2D απεικόνιση
            
            # Δημιουργούμε τον Canvas του Tkinter που θα φιλοξενήσει τη Figure
            canvas = FigureCanvasTkAgg(fig, master=tab_frame)
            # Τοποθετούμε τον καμβά μέσα στο tab_frame
            canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
            # Προσθέτουμε και μία μπάρα εργαλείων του Matplotlib με τυπικά κουμπιά ενεργειών.
            toolbar = NavigationToolbar2Tk(canvas, tab_frame)
            toolbar.update() 
            canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True) # Επανατοποθέτηση μετά την toolbar

            # Αποθηκεύουμε τα στοιχεία της καρτέλας
            self.plot_tabs_dict[key] = {"fig": fig, "ax": ax, "canvas": canvas, "toolbar": toolbar}
        
        # Καλούμε μια μέθοδο για να βάλουμε αρχικούς τίτλους κλπ. στα γραφήματα
        self.initialize_plots()
        
        # Επαναφορά (ή αρχικοποίηση) των δεδομένων για την καμπύλη σύγκλισης.
        self.convergence_data = {'iterations': [], 'fitness': []}

    
            
    def initialize_plots(self):
        """
            Η μέθοδος αρχικοποιεί όλα τα γραφήματα που έχουν δημιουργηθεί και
            για κάθε γράφημα προβαίνει στις εξής ενέργειες:
            - Καθαρίζει τυχόν προγούμενα δεδομένα απο την επιφάνεια σχεδίασης,
            - Καθορίζει του άξονες με τους τίτλους και τις ετικέτες των αξόνων,
            - Εφαρμόζει το τρέχων στύλ της εφαρμογής στα γραφήματα.
        """
        # Ελέγχουμε αν το λεξικό δεν έχει αρχικοποιηθεί ή είναι κενό τότε
        # κάνουμε return.
        if not hasattr(self, 'plot_tabs_dict') or not self.plot_tabs_dict:
            return

        # Αλλιώς διατρέχουμε κάθε ζεύγος K-V του λεξικού self.plot_tabs_dict 
        for plot_key, elements in self.plot_tabs_dict.items():
            ax = elements["ax"]
            fig = elements["fig"]
            # Με την clear() αφαιρούνται όλα τα στοιχεία που έχουν σχεδιαστεί
            # πάνω στους άξονες.
            ax.clear()

            #--- Ακολούθως αναλόγως του είδους του γραφήματος γίνεται και αντίστοιχη αρχικοποίηση γραφήματος.
            if plot_key == "3d_view":
                ax.set_title('3D View (Benchmark Function with Search Agents) ')
                ax.set_xlabel('X1')
                ax.set_ylabel('X2')
                ax.set_zlabel('Fitness Value')                
                self.plotted_3d_surface = None # Επιφάνεια Συνάρτησης Καταλληλότητας
                self.scatter_3d_wolves = None # Θέσεις Λύκων
            elif plot_key == "top_view":
                ax.set_title('Top View (Benchmark Function & Agents)')
                ax.set_xlabel('X1')
                ax.set_ylabel('X2')
                ax.set_aspect('equal', adjustable='box')
                if self.plotted_top_view_colorbar: 
                    try: self.plotted_top_view_colorbar.remove()
                    except: pass
                    self.plotted_top_view_colorbar = None
                self.plotted_top_view_contour = None
                self.scatter_top_view_wolves = None
            elif plot_key == "convergence":
                ax.set_title('Convergence Curve (Best Fitness)')
                ax.set_xlabel('Iteration')
                ax.set_ylabel('Best Fitness')
            
            self._apply_plot_style(ax, fig, plot_key) 
            elements["canvas"].draw_idle()
        # Κάνουμε reset τον canvas αφαιρώντας την καμπύλη και όλα τα σχεδιασμένα 
        # δεδομένα της καμπύλης σύγκλισης προκειμένου να σχεδιαστεί εκ νέου
        # η νέα καμπύλη κατα την εκτέλεση του νέου RUN του GWO.
        self.convergence_data = {'iterations': [], 'fitness': []}

    def initialize_single_plot_axes(self, plot_key, benchmark_obj):
        """
            Αρχικοποιεί τους άξονες ενός συγκεκριμένους γραφήματος (που προσδιορίζεται απο το Plot key),
            θέτωντας τους τίτλους και τις ετικέτες του και εφαρμόζοντας το τρέχον οπτικό στύλ.

            Args:
                - plot_key(str): Το κλειδί του γραφήματος (πχ top_view) που θα αρχικοποιηθεί. 
                - benchmark_obj (BenchmarkFunction): Το αντικείμενο της κλάσης BenchmarkFunction που αντιστοιχεί 
                                                     στην τρέχουσα συνάρτηση αξιολόγησης.
        """

        # Ελέγχουμε αν υπάρχει το λεξικό με τις παραμέτρους του γραφήματος και οτι περιλαμβάνεται ώς κλειδί
        # το plot_key που έχει περάσει ώς όρισμα στην συνάρτηση. Αν δεν πληρούνται όλες οι συνθήκες επιστρέφουμε.
        if not hasattr(self, 'plot_tabs_dict') or plot_key not in self.plot_tabs_dict:
            return

        # Λαμβάνουμε το configuration για το συγκεκριμένο κλειδί που είναι επίσης ένα λεξικό
        # και προσπελάυνουμε το λεξικό elements και λαμβάνουμε τις τιμές για τα κλειδιά ax, fig, canvas
        elements = self.plot_tabs_dict[plot_key]
        ax, fig, canvas = elements["ax"], elements["fig"], elements["canvas"]        

        # Για το 3D θέτουμε τα βασικά στοιχεία των αξόνων
        if plot_key == "3d_view":
            ax.set_title(f"{benchmark_obj.get_name()} Function - 3D View")
            ax.set_xlabel('X1')
            ax.set_ylabel('X2')
            ax.set_zlabel('Fitness Value')
        elif plot_key == "top_view":
            ax.set_title(f"{benchmark_obj.get_name()} Function - Top View")            
            ax.set_xlabel('X1')
            ax.set_ylabel('X2')
            ax.set_aspect('equal', adjustable='box')
            if self.plotted_top_view_colorbar: 
                 self.plotted_top_view_colorbar.set_label("Fitness Value")

        self._apply_plot_style(ax, fig, plot_key) 
        canvas.draw_idle()

    def _apply_plot_style(self, ax, fig, plot_key):
        """
            Εφαρμόζει το τρέχον στύλ (Χρώματα Φόντου, Κειμένου, Grid, Κλπ) σε
            κάποιο γράφημα. Την καλούμε στην αρχικοποιήση των γραφημάτων όταν 
            αλλαζει το θέμα της εφαρμογής ή το φόντο των γραφημάτων απο το toggle button

            Args:
            ax (matplotlib.axes.Axes): Αντικείμενο Axes του γραφήματος στο οποίο θα εφαρμοστεί το στύλ.
            fig (matplotlib.figure.Figure): Αντικείμενο Figure του Γραφήματος.
            plot_key(str): Το Κλειδί που αντιστοιχέι στο όνομα του γραφήματος (π.χ top_view)
        """
        # --- Εφαρμογή Χρωμάτος Φόντου ---
        # Εφαρμόζονται τα χρώματα των Figure (γύρω απο την γραφική παραάσταση) 
        # και Axes (άξονες - περιοχή σχεδίασης γραφικής παράστασης).
        fig.set_facecolor(self.plot_fig_bg_color)
        ax.set_facecolor(self.plot_axes_bg_color)

        # --- Καθορισμός Χρωμάτων Κειμένου, Grid και Γραμμών Αξόνων ---
        #Λαμβάνουμε το όνομα του τρέχοντος θέματος της εφαρμογής.
        current_ttk_theme_name = self.style.theme.name
        # Μεταβλητή Boolean αν το θέμα είναι σκούρο
        is_ttk_dark = current_ttk_theme_name in self.dark_ttk_themes        
        # Καθοριζουμε τα χρώματα με βάση το θέμα της εφαρμογής και του φόντου του γραφήματος.
        # Αν ο χρήστης έχει επιλέξει σκούρο φόντο τότε:
        if self.plot_dark_background_var.get():
            text_color = 'lightgrey' # Χρώμα κειμένου
            title_color = 'white'    # Χρώμα Τίτλου
            grid_color = '#666666' # Χρώμα Πλέγματος
            spine_color = 'lightgrey' # Χρώμα Αξόνων
            plot_line_color = 'cyan' if plot_key == "convergence" else 'red' # Χρώμα Καμπύλης
        elif is_ttk_dark: # Αν το θέμα της εφαρμογής ειναι σκούρο και το φόντο ανοιχτό τοτε:
            text_color = 'lightgrey' # Χρώμα κειμένου
            title_color = 'white'    # Χρώμα Τίτλου
            grid_color = '#555555' # Χρώμα Πλέγματος
            spine_color = 'lightgrey' # Χρώμα Αξόνων
            plot_line_color = 'cyan' if plot_key == "convergence" else 'red' # Χρώμα Καμπύλης
        else: # Αν το Θέμα ειναι ανοιχτό και το φόντο ειναι ανοιχτόχρωμο τότε προσαμόζουμε 
            #τα χρώματα των αξόνων , του πλέγματος κλπ για βέλτιστη UX:
            text_color = '#333333' # Χρώμα κειμένου
            title_color = 'black'    # Χρώμα Τίτλου
            grid_color = 'lightgrey' # Χρώμα Πλέγματος
            spine_color = '#333333' # Χρώμα Αξόνων
            plot_line_color = 'dodgerblue' if plot_key == "convergence" else 'red' # Χρώμα Καμπύλης

        # --- Εφαρμογή των χρωμάτων στα στοιχεία του γραφήματος ---
        # Τίτλος του γραφήματος
        ax.title.set_color(title_color)
        # Ετικέτες των αξόνων (Χ,Υ)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        # Αν υπάρχει και άξονας Z τότε καθορίζουμε το χρώμα του:
        if hasattr(ax, 'zaxis'):
            ax.zaxis.label.set_color(text_color)
            ax.tick_params(axis='z', colors=text_color)

        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        for spine in ax.spines.values():
            spine.set_edgecolor(spine_color)
        # Εμφανίζουμε το πλέγμα και θέτουμε την μορφή του, το χρώμα του και την πυκνότητα του.
        ax.grid(True, linestyle='--', color=grid_color, alpha=0.6)        
       
        # Ακολούθως προβαίνουμε σε επιμέρους μορφοποίηση αναλόγως του είδους του γραφήματος.
        if plot_key == "convergence" and ax.lines:
            for line in ax.lines: 
                line.set_color(plot_line_color)        
        
        if plot_key == "top_view" and hasattr(self, 'plotted_top_view_colorbar') and self.plotted_top_view_colorbar:
            self.plotted_top_view_colorbar.ax.yaxis.label.set_color(text_color)
            self.plotted_top_view_colorbar.ax.tick_params(axis='y', colors=text_color)

            for spine in self.plotted_top_view_colorbar.ax.spines.values():
                spine.set_edgecolor(spine_color)
        # Εφαρμόζουμε tight_layout() για να αποφύγουμε επικάλυψη ετικετών
        # Επειδή η tight_layout() προκαλεί εξαιρέσεις τις διαχειριζόμαστε 
        # τυπώνοντας ένα μύνημα στο log area για να ενημερωθεί ο χρήστης.
        try:
            fig.tight_layout(pad=1.5)
        except Exception as e:
            print(f"Error plotting the graph's: {e}")
            self.log_message(f"Error plotting the graph's: {e}")
            pass 

   # 4. Μέθοδοι Ενημέρωσης Περιεχομένου Γραφημάτων =====================================================================

    def draw_benchmark_static_backgrounds(self, benchmark_obj):

        """
            Η συνάρτηση σχεδιάζει την συνάρτηση αξιολόγησης στα γραφήματα 3D View 
            και Top View. Καλείται μία φορά όταν αλλάζει η συνάρτηση ή όταν ξεκινά
            ο αλγόριθμος για πρώτη φορά.

            Args:
                benchmark_obj (BenchmarkFunction): Ένα αντικείμενο της κλάσης BenchmarkFunction που αποτελεί
                και την συνάρτηση αξιολόγηση η οποία θα σχεδιαστεί.
        """

        # Ελέγχουμε αν υπάρχεί το λεξικό με τις ρυθμίσεις σχεδίασης των γραφημάτων
        # Αν δεν υπάρχουν τότε απλά γίνεται return απο την συνάρτηση
        if not hasattr(self, "plot_tabs_dict") or not self.plot_tabs_dict:
            print("DEBUG: Plot configurations dictionary doesn't exists.")
            return        
        
        # Ελεγχος αν έχουμε πάνω απο δύο διαστάσεις του προβλήματος και άρα μαζί με την διάσταση 
        # που αντιστοιχεί στις τιμές καταλληλότητας πάνω απο 3 διαστάσεις. Σε αυτή την περίπτωση
        # δεν μπορούμε να σχεδιάσουμε τα χωρικά γραφήματα και καλούμε την clear() για καθαρισμό των
        # σχεδιάσεων απο προηγούμενες εκτελέσεις.
        if benchmark_obj.dimensions != 2:
            if "3d_view" in self.plot_tabs_dict:
                elements = self.plot_tabs_dict["3d_view"]
                ax_3d, canvas_3d = elements["ax"], elements["canvas"]
                ax_3d.clear()                
                self.initialize_single_plot_axes("3d_view", benchmark_obj)                
                self.plotted_3d_surface = None
                canvas_3d.draw_idle()
            if "top_view" in self.plot_tabs_dict:
                elements = self.plot_tabs_dict["top_view"]
                ax_top, canvas_top = elements["ax"], elements["canvas"]
                ax_top.clear()
                if self.plotted_top_view_colorbar:
                    try: 
                        self.plotted_top_view_colorbar.remove()
                    except: 
                        pass
                    self.plotted_top_view_colorbar = None                
                self.initialize_single_plot_axes("top_view", benchmark_obj)                
                self.plotted_top_view_contour = None
                canvas_top.draw_idle()

            self.current_benchmark_object_for_spatial_plot = None
            return # Σταματάμε εδώ, αφού δεν θα γίνει σχεδίαση
        # Σε άλλη περίπτωση, δηλαδή έχουμε 3 διαστάσεις, λαμβάνουμε το αντικείμενο
        # της συνάρτησης αξιολόγησης και το αποθηκέυμε στο πεδίο self.current_benchmark_object_for_spatial_plot.
        #print(f"DEBUG: Drawing static background for {benchmark_obj.name}")
        self.current_benchmark_object_for_spatial_plot = benchmark_obj

        # Ακολούθως παίρνουμε τα ορία της συνάρτησης και τα αποθηκεύομε σε αντίστοιχες μεταβλητές.
        lower_bound, upper_bound = benchmark_obj.lower_bound, benchmark_obj.upper_bound
        # Καθορίζουμε ενα πλήθος απο σημεία για την δημιουργία του πλέγματος.
        num_points = 75
        # Δημιουργούνται δύο πίνακες με num_points πλήθος σημείων ομοιόμορφα κατανεμημένα ανάμεσα στα όρια.
        X1_vals = np.linspace(lower_bound, upper_bound, num_points) # []
        X2_vals = np.linspace(lower_bound, upper_bound, num_points) # []
        # Δημιουργούνται δύο δισδιάσταστατοι πίνακες με τις συνταταγμένες Χ, Υ των σημείων του πλέγματος.
        X, Y = np.meshgrid(X1_vals, X2_vals) 

        # Υπολογίζουμε τις τιμές για τον άξονα Ζ που είναι οι τιμές fitness για κάθε σημείο (x,y) του πλέγματος.
        # Αρχικά εκτελούμε αρχικοποίηση του πίνακα Ζ με μηδενικά, ίδιων διαστάσεων με το Χ (ή το Υ).
        Z = np.zeros_like(X)
        for i in range(X.shape[0]): # Για κάθε σειρά του πλέγματος
            for j in range(X.shape[1]): # Για κάθε στήλη του πλέγματος
                # καλείτει η συνάρτηση υπολογισμού της καταλληλότητας calculate_fitness() για
                # τις τρέχουσες συντεταγμένες του πλέγματος και υπολογίζεται το fitness.
                Z[i, j] = benchmark_obj.calculate_fitness([X[i, j], Y[i, j]])

        # Σχεδιάζουμε το Background του 3D View Γραφήματος της συνάρτησης αξιολόγησης.
        if "3d_view" in self.plot_tabs_dict:
            ax_3d = self.plot_tabs_dict["3d_view"]["ax"]
            canvas_3d = self.plot_tabs_dict["3d_view"]["canvas"]
            ax_3d.clear() # Καθαρισμός των αξόνων πρίν την σχεδίαση           
            # Σχεδίαση με την plot_surface() της συνάρτησης αξιολόγησης με συγκεκριμένες παραμέτρους 
            # (π.χ χρωματική παλέτα viridis, μπορούμε να διαλέξουμε και inferno)       
            self.plotted_3d_surface = ax_3d.plot_surface(X, Y, Z, cmap="viridis", alpha=0.7, edgecolor="none")
            #ax_3d.legend(loc='upper right', fontsize='small', framealpha=0.5)
            self.initialize_single_plot_axes("3d_view", benchmark_obj)
            canvas_3d.draw_idle()
        # Ομοίως για το Top View           
        if "top_view" in self.plot_tabs_dict:
            ax_top = self.plot_tabs_dict["top_view"]["ax"]
            canvas_top = self.plot_tabs_dict["top_view"]["canvas"]
            fig_top = self.plot_tabs_dict["top_view"]["fig"]
            ax_top.clear() # Καθαρισμός των αξόνων πρίν την σχεδίαση
            if self.plotted_top_view_contour: # Αφαίρεση παλαιού colorbar αν υπάρχει
                try:
                    self.plotted_top_view_colorbar.remove()
                except Exception as e:
                    #print(f"DEBUG: Error removing old colorbar: {e}")
                    self.plotted_top_view_colorbar = None
            
            self.plotted_top_view_contour = ax_top.contourf(X, Y, Z, levels=50, cmap='viridis', alpha=0.8)
            self.plotted_top_view_colorbar = fig_top.colorbar(self.plotted_top_view_contour, ax=ax_top, orientation='vertical', shrink=0.8)
            self.initialize_single_plot_axes("top_view", benchmark_obj) 
            canvas_top.draw_idle()  


    def update_convergence_plot(self, clear_only=False):
        """
            Ενημερώνει ή καθαρίζει το γράφημα της καμπύλης σύγκλισης.

            Args:
                clear_only(bool): Αν είναι True τότε γίνεται μόνο καθαρισμός του 
                γραφήματος χωρίς να σχεδιαστούν νέα δεδομένα.        
        """
        if not hasattr(self, "plot_tabs_dict") or "convergence" not in self.plot_tabs_dict:
            return
        # Προσπελαύνουμε τα δεδομένα σχεδίασης του γραφήματος
        elements = self.plot_tabs_dict["convergence"]
        ax, fig, canvas = elements["ax"], elements["fig"], elements["canvas"]
        # Καθαρίζουμε προηγούμενη σχεδίαση.
        ax.clear()

        if not clear_only and hasattr(self, 'convergence_data') and self.convergence_data['iterations'] and \
              self.convergence_data['fitness']:
            if len(self.convergence_data['iterations']) == len(self.convergence_data['fitness']):
                ax.plot(self.convergence_data['iterations'], self.convergence_data['fitness'],
                        marker='.', linestyle='-', markersize=4)
            

        ax.set_title('Convergence Curve')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Best Fitness')
        self._apply_plot_style(ax, fig, "convergence")
        canvas.draw_idle()

    def update_3d_plot_content(self, msg_data):
        """
            Η συνάρτηση καλείται σπο την process_gui_queue() όταν λαμβάνεται μύνημα τύπου "spatial_plot_data"
            και η ενεργή καρτέλα στο notebook είναι η "3D_View". Ενημερώνει το περιεχόμενο του 3D γραφήματος
            (καρτέλα 3D View) με τις τρέχουσες θέσεις των πρακτόρων αναζήτησης (λύκων).

            Args: msg_data(dict): Λεξικό με τα δεδομένα για την ενημέρωση του γραφήματος.
        """
        if "3d_view" not in self.plot_tabs_dict: return
        elements = self.plot_tabs_dict["3d_view"]
        ax, canvas = elements["ax"], elements["canvas"]

        positions = msg_data.get("wolves_positions")
        fitness_values = msg_data.get("wolves_fitness") 

        if positions is None or fitness_values is None or positions.shape[1] < 2:            
            return
        
        if positions.shape[0] != fitness_values.shape[0]:           
            return

        # Αφαίρεσε του λύκους απο το γράφημα
        if self.scatter_3d_wolves:
            try:
                self.scatter_3d_wolves.remove()
            except: 
                pass
            self.scatter_3d_wolves = None

        # Σχεδίασε του λύκους στο γράφημα με βάση τις συντεταγμένες των θέσεων τους.        
        x_coords, y_coords = positions[:, 0], positions[:, 1]
        z_coords = fitness_values
        self.scatter_3d_wolves = ax.scatter(x_coords, y_coords, z_coords, color='red', s=30, depthshade=True, label="Wolves")               
        canvas.draw_idle()
      
    
    def update_top_view_plot_content(self, msg_data):
        """
            Ομοίως με την update_3d_plot_content(), ενημερώνει το γράφημα με τις θέσεις των λύκων.

            Args: msg_data(dict): Λεξικό με τα δεδομένα για την ενημέρωση του γραφήματος.
        """
        if "top_view" not in self.plot_tabs_dict: return
        elements = self.plot_tabs_dict["top_view"]
        ax, canvas = elements["ax"], elements["canvas"]

        positions = msg_data.get("wolves_positions")
        if positions is None or positions.shape[1] < 2:            
            return

        # # Αφαίρεσε του λύκους απο το γράφημα
        if self.scatter_top_view_wolves:
            try:
                self.scatter_top_view_wolves.remove()
            except:
                pass
            self.scatter_top_view_wolves = None
        
        self.scatter_top_view_wolves = ax.scatter(positions[:, 0], positions[:, 1], color='red', s=30, label="Wolves")        
        canvas.draw_idle()

    
    # 5. Μέθοδοι Χειρισμού Γεγονότων (Events) ==========================================================================

    def on_benchmark_select(self, event=None):
        """
            Καλείται όταν ο χρήστης επιλέξει σπο το combobox καποια συνάρτηση αξιολόγησης
            απο αυτές που έχουμε στην λίστα με τις συναρτήσεις σταθερών διαστάσεων τότε το 
            πεδίο εισαγωγής διαστάσεων απενεργοποιείται και τοποθετείται αυτόματα η τιμή 2
            αλλιώς το πεδίο παραμένει ενεργό για εισαγωγή της εισόδου του χρήστη.
        """
        selected_function = self.parameters_dict["benchmark"].get()
        if selected_function in self.fixed_dim_functions:
            self.parameters_dict["dimensions"].set("2")
            self.dimensions_entry.config(state="disabled")
        else:
            self.dimensions_entry.config(state="normal")   

    def on_theme_select(self, event=None, update_plots=True):
        """
            Η Συνάρτηση αυτή λαμβάνει το θέμα που επέλεξε ο χρήστης απο το
            combobox επιλογης θεμάτων και το ttkbootstrap το εφαρμόζει σε όλη την εφαρμογή
        """
        selected_theme_name = self.theme_combo.get()
        self.style.theme_use(selected_theme_name)
        if update_plots and hasattr(self, 'plot_tabs_dict') and self.plot_tabs_dict:
            # Εφαρμογή του στύλ του θέματος της εφαρμογής στα γραφήματα.
            for plot_key in self.plot_tabs_dict:
                elements = self.plot_tabs_dict[plot_key]
                self._apply_plot_style(elements["ax"], elements["fig"], plot_key)
                elements["canvas"].draw_idle()

    def on_plot_background_toggle(self):
        """
            Η μέθοδος καλείται όταν ο Χρήστης επιλέξει μία απο τις 2 καταστάσεις
            του toggle button για την επιλογή dark/light φόντου γραφικών παραστάσεων.
        """ 
        # Αρχικά καλείται η private μέθοδος _update_plot_bg_colors() η οποία διαβάζει 
        # την τρέχουσα τιμή του πεδίου self.plot_dark_background_var και ορίζει τα πεδία 
        # self.plot_fig_bg_color και self.plot_axes_bg_color.
        self._update_plot_bg_colors()
        # Εμφανίζουμε μύνημα στο Log frame για την ενημέρωση του Χρήστη οτι άλλαξε το φόντο.
        self.log_message(f"{'Dark' if self.plot_dark_background_var.get() else 'Light'} plot background selected.")
        # Έλεγχος οτι υπάρχει και οτι δεν είναι κενό το λεξικό που περιέχει τις αναφορές στα στοιχεία 
        # (figure, axes, canvas) κάθε καρτέλας του γραφήματος.
        if hasattr(self, 'plot_tabs_dict') and self.plot_tabs_dict:

            current_app_theme_is_dark = self.style.theme.name in self.dark_ttk_themes
            # Για κάθε κλειδί του λεξικού με τις ρυμίσεις των καρτελών του Notebook:
            for plot_key in self.plot_tabs_dict:
                # Παίρνουμε το Value που ειναι ένα λεξικό με κλειδία fig, ax, canvas
                elements = self.plot_tabs_dict[plot_key]
                # Καλούμε την συνάρτηση _apply_plot_style() περνώντας ώς όρισμα τα values των keys "ax", "fig"
                # καθώς και το key των ρυθμίσεων (πχ convergence ή 3d_view ή top_view)
                self._apply_plot_style(elements["ax"], elements["fig"], plot_key)
                # Ενημέρωση του canvas για την επανασχεδίαση του γραφήματος με το νέο στύλ (φόντο, συμβατά χρώματα αξόνων κλπ)
                elements["canvas"].draw_idle()    
    
    # 6. Μέθοδοι Σχετικές με την Εκτέλεση του GWO και την Επικοινωνία μεταξύ ων Νημάτων ================================

    def start_gwo_thread_wrapper(self):
        """
            Αυτή η συνάρτηση εκτελεί τον αλγόριθμο σε ένα νέο νήμα, διαβάζει και επικυρώνει τις τιμές
            απο την φόρμα εισόδου των παραμέτρων και ενημέρωνει την κατάσταση των κουμπιών.
        """
        # Ελέγχουμε αν υπάρχει ηδη το thread για την εκτέλεση του GWO και τρέχει.
        if self.gwo_thread and self.gwo_thread.is_alive():
            messagebox.showwarning("The GWO is already running.")
            return        
        # Συλλέγουμε και επικυρώνουμε τις τιμές των παραμέτρων απο την φόρμα.
        try:
            # Λεξικό για την αποθήκευση των παραμέτρων.
            temp_parameters = {}
            self.plot_update_counter = 0

            # Διατρέχουμε το λεξικό self.parameters_dict που περιέχει τις μεταβλητές StringVar απο τα πεδία της φόρμας.
            for key, value in self.parameters_dict.items():
                # Για κάθε ζεύγος K-V του λεξικο parameters_dict αποθηκεύομε το ζεύγος στο λεξικό parameters.
                temp_parameters[key]=value.get()

            #Ακολούθως εκτελούμε επικύρωση και μετατροπή τύπων των τιμών των παραμέτρων
            benchmark_name = str(temp_parameters["benchmark"])
            # Αν η συνάρτηση αξιολόγησης δεν είναι στην λίστα με τις συναρτήσεις αξιολόγησης
            # ή έχει τιμή το Placeholder του πεδίου ενημερώνουμε τον χρήστη για το λάθος.
            if not benchmark_name or benchmark_name == "Select a function...":
                messagebox.showerror("Invalid Input", "Please select a valid benchmark function")
                return

            # Μετατρέπουμε ακολούθως τους τύπους των τιμών των παραμέτρων απο string σε σωστούς τύπους (int, float, boolean).
            dimensions = int(temp_parameters["dimensions"])
            wolves_num = int(temp_parameters["wolves"])
            max_iter = int(temp_parameters["max_iter"])
            min_std_dev = float(temp_parameters["min_std_dev"])            
            num_runs = int(temp_parameters["runs"])
            plot_enabled_for_gwo = self.enable_spatial_live_update_var.get()            

             # Ελέγχουμε αν ο χρήστης έχει επιλέξει τον ελάχιστο αριθμό των 3 λύκων 
            # που απαιτείται για να εκτελεστεί ο αλγόριθμος.
            if wolves_num < 3:
                messagebox.showerror("Invalid Input", "Choose at least 3 wolves")
                return            
            # Σε περίπτωση επιλογής απο τον χρήστη συνάρτησης σταθερών διαστάσεων τοποθετούμε στην μεταβλητη 
            # dimensions την τιμή 2 σε συμφωνία με την ανάθεση στο κατάλληλο widget να εμφανίσει την τιμή 2.
            if benchmark_name in self.fixed_dim_functions:
                dimensions = 2

            if max_iter <= 0:
                messagebox.showerror("Invalid Input", "Max Iterations must be a positive integer.")
                return
            
            if num_runs <= 0:
                messagebox.showerror("Invalid Input", "Number of runs must be a positive integer.")

        except ValueError as ex:
            messagebox.showerror("Invalid Input", f"error in parameter value:  {ex}.\n Check the input fields")
            return
        
        # Προετοιμασία GUI 
        self.run_button.config(state=DISABLED) # Απενεργοποίηση του κουμπιού RUN.
        self.stop_button.config(state=NORMAL) # Ενεργοποίηση του κουμπιού STOP.
        # Κάνουμε reset το event για να επιτραπεί η εκτέλεση του αλγορίθμου (δεν έχει πατηθεί STOP).
        self.stop_event.clear()

        self.cumulative_execution_time = 0.0
        self.exec_time_label.config(text="0.0000")
        # Καθάρισε τα δεδομένα της καμπύλης σύγκλισης για τη νέα εκτέλεση
        self.convergence_data = {'iterations': [], 'fitness': []}
        self.update_convergence_plot(clear_only=True) # Καθάρισε το γράφημα

        current_benchmark_name = getattr(self.current_benchmark_object_for_spatial_plot, 'name', None)
        current_benchmark_dims = getattr(self.current_benchmark_object_for_spatial_plot, 'dimensions', None)

        if benchmark_name != current_benchmark_name or \
           dimensions != current_benchmark_dims or \
           self.current_benchmark_object_for_spatial_plot is None:
                        
            plot_benchmark_obj = BenchmarkFunction(benchmark_name, dimensions)
            self.draw_benchmark_static_backgrounds(plot_benchmark_obj)
        elif dimensions != 2 and self.current_benchmark_object_for_spatial_plot is not None:
            plot_benchmark_obj = BenchmarkFunction(benchmark_name, dimensions) # Will trigger clearing
            self.draw_benchmark_static_backgrounds(plot_benchmark_obj)


        self.log_message(f"--- Starting GWO for {benchmark_name} function ---")

        # Δημιουργία και Εκκίνηση του Thread. target: Η συνάρτηση που θα εκτελεστεί μέσα στο thread.
        # args: Μια πλειάδα (tuple) με τα ορίσματα που θα περάσουμε στη συνάρτηση target.
        self.gwo_thread = threading.Thread(
            target = self.run_gwo_algorithm,
            args=(benchmark_name, dimensions, wolves_num, max_iter, min_std_dev, num_runs, plot_enabled_for_gwo)
        )
        # Αν κλείσει η διεργασία του GUI θα τερματιστεί και το thread.
        self.gwo_thread.daemon = True
        # Εκκίνηση του thread.
        self.gwo_thread.start()  


    def run_gwo_algorithm(self, benchmark_name, dimensions, wolves_num, max_iter, min_std_dev, num_runs, plot_enabled):
        """
        Εκτελεί τον αλγόριθμο GWO σε ένα ξεχωριστό thread  για να μην παγώνει το GUI. 
        Στέλνει ενημερώσεις κατάστασης και αποτελέσματα πίσω στο κυρίως thread του GUI μέσω μίας thread-safe queue.

        Args:
            benchmark_name (str):  Συνάρτηση αξιολόγησης.
            dimensions (int): Πλήθος διαστάσεων του προβλήματος.
            wolves_num (int): Πλήθος πρακτόρων (λύκων).
            max_iter (int): Μέγιστος αριθμός επαναλήψεων.
            min_std_dev (float): Κατώφλι τυπικής απόκλισης.            
            num_runs (int): Συνολικός αριθμός εκτελέσεων που θα γίνουν.
            plot_enabled (bool): Επιλογή σχεδίασης γραφικών παραστάσεων.
        """
        final_results_for_gui = None
        try:
            # Δημιουργούμε το directory αν δεν υπάρχει ήδη στο οποίο θα αποθηκευτεί το csv αρχείο με τα αποτελέσματα.
            results_folder = f"gui_results//results_with_{wolves_num}_agents_gui"
            results_folder = os.path.join("gui_results", f"results_with_{wolves_num}_agents_gui")
            os.makedirs(results_folder, exist_ok=True)
            # Λίστα για την αποθήκευση των αποτελεσμάτων σε κάθε run του αλγορίθμου.
            results_list_for_csv = []

            # Επανάληψη για την εκτέλεση του αλγορίθμου για το πλήθος των run που έχει ορίσει ο χρήστης.
            for i in range(num_runs):
                # Ελεγχος αν ο χρήστης έχει πατήσει το κουμπί STOP.
                if self.stop_event.is_set():
                    # Αν ναι τοτε στέλνουμε ένα μύνημα στο log οτι ο χρήστης ακύρωσε την εκτέλεση.
                    self.gui_queue.put(("log", "Run aborted by user."))
                    break

                 # Αποστολή μυνήματος στην ουρά για την εκκαθάριση της καμπύλης σύγκλισης.
                self.gui_queue.put(("clear_convergence_for_new_run", {"current_run": i + 1, "total_runs": num_runs}))
                
                # Αλλιώς στέλνουμε στο GUI ενημέρωση για τον αριθμό του τρέχοντος RUN.
                self.gui_queue.put(("run_update", (i + 1, num_runs)))
                # Δημιουργούμε ενα αντικείμενο της κλάσης BenchmarkFunction.
                benchmark_func = BenchmarkFunction(benchmark_name, dimensions)
        
                # Καλούμε την συνάρτηση GWO(), εκτελούμε τον αλγόριθμο με τις παραμέτρους του χρήστη και αποθηκευουμε τα αποτελέσματα
                # σε ένα λεξικό run_results.
                run_results = GWO(
                    wolves_num, 
                    max_iter, 
                    min_std_dev, 
                    benchmark_func,
                    plot_enabled, 
                    # Συνάρτηση που ενημερώνει ασύγχρονα το νήμα του GUI απο το τρέχων νήμα του αλγορίθμου.
                    gui_callback=self.gui_callback_from_thread,
                    # Αντικείμενο threading.Event για εξωτερική διακοπή (Κουμπί STOP).
                    stop_event=self.stop_event
                )

                if "error" in run_results: 
                    self.gui_queue.put(("log", f"GWO Error: {run_results['error']}"))
                    break
                
                run_results['run'] = i + 1 # Προσθέτουμε +1 στο RUN γιατί ξεκινάει απο το 0.
                # Προσθέτουμε το λεξικό που επέστρεψε το GWO() σαν στοιχείο στο τέλος της λίστας π.χ [{},{}] με τα αποτελέσματα.
                results_list_for_csv.append(run_results)
                # Κρατάμε ένα αντίγραφο των αποτελεσμάτων για χρήση στο GUI
                final_results_for_gui = run_results.copy()

                # Παίρνουμε τον χρόνο εκτέλεσης απο τα αποτελέσματα του
                # αλγορίθμου και τον στέλνουμε στην ουρά για κατανάλωση απο το thread του GUI.
                current_run_time = run_results.get("gwo_time", 0.0)
                self.gui_queue.put(("run_completed_stats", {"gwo_time": current_run_time}))
                
                # Παίρνουμε το value του Key min_fitness, αν δεν υπάρχει στο λεξικό τοτε παίρνουμε το Ν/Α.
                fitness = run_results.get('min_fitness', 'N/A')
                # Χρησιμοποιούμε try-except για την περίπτωση που το fitness δεν είναι αριθμός.
                try:
                    # φτιάχνουμε ενα string με την τιμή του fitness σε επιστημονική μορφή με 4 δεκαδικά π.χ 1.0787E-10
                    # Αν για κάποιο λόγο το fitness δεν εχει σωστό τύπο (π.χ ειναι το Ν/Α) ή σωστή τιμή
                    #  θα πεταχτεί εξαίρεση και θα την πιάσουμε.
                    log_msg = f"Run {i+1} finished. Min Fitness: {fitness:.4e}"
                except (TypeError, ValueError):
                    # Σε περίπτωση εξαίρεσης προσθέτουμε στο string την υπάρχουσα τιμή fitness οπως είναι π.χ Ν/Α.                 
                    log_msg = f"Run {i+1} finished. Min Fitness: {fitness}"
                # Ακολούθως στέλνουμε στο Thread του GUI μεσω της ουράς το ενημερωτικό μύνημα με το tag "log".
                self.gui_queue.put(("log", log_msg))                     
            
            #Αν η λίστα με τα αποτελέσματα δεν είναι κενή και ο χρήστης δεν έχει πατήσει το κουμπί STOP.
            if results_list_for_csv and not self.stop_event.is_set():
                # Δημιουργούμε το αρχείο csv για τα αποτελέσματα.
                csv_filename = os.path.join(results_folder, f"gwo_results_{benchmark_name}.csv")
                # Παίρνουμε τα ονομάτα των πεδίων.
                fieldnames = list(results_list_for_csv[0].keys())
                # Ανοίγουμε το αρχείο για εγγραφή.
                with open(csv_filename, mode="w", newline="", encoding='utf-8') as file:
                    # Δημιουργούμε ένα αντικείμενο csv.DictWriter.
                    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
                    # Γράφουμε στο αρχείο την πρώτη γραμμή με τις επικεφαλίδες.
                    writer.writeheader()
                    # Εν συνεχεία γράφουμε και τα αποτελέσματα απο την λίστα των αποτελεσμάτων.
                    writer.writerows(results_list_for_csv)
                # Στέλνουμε ενα μύνημα στο GUI μεσω της ουρας για την επιτυχή αποθήκευση των αποτελεσμάτων στο αρχείο.
                self.gui_queue.put(("log", f"Results saved to {csv_filename}"))            
        # Αν προκληθεί οποιαδήποτε εξαίρεση την πιάνουμε και στέλνουμε μύνημα στο GUI.

        except Exception as e:            
            self.gui_queue.put(("log", f"An unexpected error occurred in GWO thread: {e}"))
        # Σε κάθε περίπτωση στέλνουμε μύνημα ολοκλήρωσης της εκτέλεσης στο GUI μέσω της ουράς.
        finally:            
            self.gui_queue.put(("all_runs_finished", final_results_for_gui))


    def process_gui_queue(self):        
        """
            Η συνάρτηση διαχειρίζεται τα μυνήματα απο την thread safe Ουρα που χρησιμοποιούμε για την επικοινωνία
            μεταξύ των νημάτων του GWO και του GUI. Καλείται περιοδικά απο το tKinter event loop και διαβάζει όλα 
            τα διαθέσιμα μυνήματα απο την ουρά και ενημερώνει τα αντίστοιχα GUI Widgets.            
        """
        try:
              
            for _ in range(10): # Κατανάλωσε εώς 10 μυνήματα απο την ουρά
                msg_type = None  # Αρχικοποίηση τύπου μυνήματος
                msg_data = None  # Αρχικοποίηση δεδομένων μυνήματος
                message_successfully_retrieved = False

                try:             
                    # Λήψη μηνύματος από την ουρά χωρίς να μπλοκάρει το νήμα αν η Ουρα είναι άδεια 
                    # προκαλείται queue.Empty Exception.
                    message_item = self.gui_queue.get_nowait()                     
                    # Έλεγχος αν το message_item είναι το αναμενόμενο tuple (τύπος, δεδομένα).
                    if isinstance(message_item, tuple) and len(message_item) == 2:
                        #Αποθηκεύουμε τα στοιχεία του tuple σε μεταβλητές
                        msg_type, msg_data = message_item
                        # Ενημέρωνουμε μία σημαία για επιτυχή λήψη μυνήματος
                        message_successfully_retrieved = True
                    else:
                        # Αλλιώς τυπώνουμε στην κονσόλα για σκοπούς debuging.
                        error_log_msg = f"Error with message: {message_item}"
                        print(error_log_msg)
                        # Και το εμφανίζουμε και στο log widget για ενημέρωση του Χρήστη.
                        self.log_message(error_log_msg)
                # Σε περίπτωση που η ουρά ειναι και προκλαίεται εξαίρεση, πιάνουμε την εξαίρεση και σπάμε το Loop.        
                except queue.Empty:
                    break
                # Σε περίπτωση έγερσης άλλης εξαίρεσης την τυπώνουμε στην κονσόλα.
                except Exception as e_get:                    
                    error_log_msg_get = f"Error: {e_get}"
                    print(error_log_msg_get)
                    # και εμφανίζουμε και το error στο Log widget του GUI.
                    self.log_message(error_log_msg_get)
                    break # Τερματίζουμε το Loop.
                # Αν η σημαία επιτυχούς λήψης ειναι True και ο τύπος μυνήματος δεν είναι None τοτε:
                if message_successfully_retrieved and msg_type is not None:
                    # Αν είναι μύνημα τύπου "log".
                    if msg_type == "log":
                        # Εμφανίζουμε στο Log Widget του GUI το Μύνημα για να ενημερωθεί ο Χρήστης.
                        self.log_message(msg_data)

                    # Αν είναι μύνημα τύπου "clear_convergence_for_new_run" το οποίο 
                    # στέλνεται απο το νήμα του GWO στην αρχή κάθε RUN για να γίνει clear() 
                    # στην καμπύλη σύγκλισης απο τα παλία δεδομένα.
                    elif msg_type == "clear_convergence_for_new_run":
                        # Ελέγχουμε αν είναι ενεργοποιημένο το Toggle Button για την εμφάνιση της καμπύλης σύγκλισης καταλληλότητας
                        if self.enable_convergence_plot_var.get():
                            # Εμφανίζουμε στο Log Widget μύνημα στο Χρήστη για την εκκαθάριση του προηγούμενου γραφήματος
                            self.log_message(f"Clearing convergence data for new run: {msg_data['current_run']}/{msg_data['total_runs']}")
                            # Μηδενίζουμε τα δεδομένα του γραφήματος της σύγκλισης με την εκ νέου αρχικοποίηση της μεταβλητής convergence_data
                            self.convergence_data = {'iterations': [], 'fitness': []}
                            # Κλήση της μεθόδου update_convergence_plot() για την εκτέλεση του clear().
                            self.update_convergence_plot(clear_only=True)
                    
                    # Αν είναι μύνημα τύπου "run_update", που ενημερώνει το GUI για την έναρξη του 
                    # νέου RUN, τότε: 
                    elif msg_type == "run_update":                    
                        # Ελέγχουμε ομοίως με πρίν τον τύπο δεδομένων του μυνήματος (tuple) και το μέγεθος του
                        if isinstance(msg_data, tuple) and len(msg_data) == 2:
                            # Εξάγουμε τα δεδομένα του tuple
                            current_run, total_runs = msg_data
                            # Ενημέρωνουμε το αντίστοιχο Label με την τιμή του τρέχοντος RUN για να το δει ο Χρήστης.
                            self.current_run_label.config(text=f"{current_run}/{total_runs}")
                            # Μηδενίζουμε την πρόοδο της Progress Bar για το νέο run.
                            self.progress_bar['value'] = 0
                        else:
                            # Σε άλλη περίπτωση εμφανίζουμε μυνήματος σφάλματος στην κονσόλα και στο log widget.
                            log_entry = f"Error with message: Expected tuple of 2, got: {type(msg_data)}, Value: {msg_data}"
                            self.log_message(log_entry) 
                            print(log_entry) # στην κονσόλα

                    # Αν είναι μύνημα τύπου "progress_update".     
                    elif msg_type == "progress_update":                    
                        # Ενημέρωση progress bar μέσα στο RUN.
                        iteration = msg_data.get("iteration", 0)
                        max_iterations = msg_data.get("max_iterations", 1)  # Αποφυγή διαίρεσης με το 0.
                        alpha_fitness = msg_data.get("alpha_fitness", "N/A")
                        std_dev = msg_data.get("std_dev", "N/A")
                        
                        # Ενημερώνουμε την ετικέτα με τον τρέχοντα αριθμό επανάληψης.
                        self.current_iter_label.config(text=f"{iteration}/{max_iterations}")                    
                    
                        # Ενημερώνουμε την ετικέτα με το καλύτερο fitness.
                        # Αν το alpha_fitness είναι αριθμός (int ή float) τότε:
                        if isinstance(alpha_fitness, (int, float)):                        
                            # μορφοποιούμε την τιμή σε επιστημονική μορφή με 4 δεκαδικά ψηφία.
                            fitness_text_value = f"{alpha_fitness:.4e}"
                        else:
                            # Αν δεν είναι αριθμός μετατρέπουμε σε string την υπάρχουσα τιμή της μεταβλητής.
                            fitness_text_value = str(alpha_fitness)
                        # Ενημερώνουμε το label του fitness.
                        self.alpha_fitness_label.config(text=fitness_text_value)

                        # Ενημερώνουμε την ετικέτα με το την τυπική απόκλιση του fitness.
                        # Αν το std_dev είναι αριθμός (int ή float) τοτε:
                        if isinstance(std_dev, (int, float)):                    
                            # Την μορφοποιούμε σε επιστημονική μορφή με 4 δεκαδικά ψηφία.
                            deviation_text_value = f"{std_dev:.4e}"
                        else:
                        # Αν δεν είναι αριθμός το μετατρέπουμε σε string όπως είναι.
                            deviation_text_value = str(std_dev)

                        # Ενημερώνουμε το label της τυπικής απόκλισης.
                        self.std_dev_label.config(text=deviation_text_value)                      
                        
                        # Υπολογίζουμε και ενημερώνουμε την μπάρα προόδου (0-100%).
                        if max_iterations > 0:                            
                            # Υπολογισμός προόδου με βάση και τη σύγκλιση
                            progress_iter = iteration / max_iterations

                            # Αν υπάρχει std_dev και είναι αριθμός, υπολογίζουμε και πρόοδο σύγκλισης
                            if isinstance(std_dev, (int, float)) and std_dev > 0:
                                try:
                                    min_std_dev_threshold = float(self.parameters_dict["min_std_dev"].get())
                                    convergence_progress = 1.0 - min(std_dev / min_std_dev_threshold, 1.0)
                                except:
                                    convergence_progress = 0.0
                            else:
                                convergence_progress = 0.0

                            # Συνδυασμός επαναλήψεων και σύγκλισης για πιο ρεαλιστική πρόοδο
                            combined_progress = (progress_iter + convergence_progress) / 2
                            self.progress_bar['value'] = combined_progress * 100


                        # Αν ειναι ενεργοποιήμενο το toggle button της καμπύλης σύγκλισης ενημέρωνουμε την καμπύλη
                        if self.enable_convergence_plot_var.get():
                            # Αν η καταλληλότητα δεν ειναι none Και ειναι σε κατάλληλο τύπο δεδομένων
                            if alpha_fitness is not None and isinstance(alpha_fitness,(int, float)):
                                # Ενημέρωνουμε τα values των κλειδιών του λεξικού που κρατάμε για τα δεδομένα της καμπύλης σύγκλισης
                                self.convergence_data['iterations'].append(iteration) # Αξονας Χ του Γραφήματος
                                self.convergence_data['fitness'].append(alpha_fitness) # Αξονας Υ του Γραφήματος
                                
                            # Διαβάζουμε την συχνότητα ενημέρωσης απο το spinbox του GUI.                            
                            try:
                                # Λαμβάνουμε την τιμή του κλειδιού plot_update_freq του λεξικού με τις τιμές των παραμέτρων
                                # που έχει εισάγει ο Χρήστης στα πεδία εισόδου για την εκτέλεση του GWO
                                update_freq_str = self.parameters_dict["plot_update_freq"].get()
                                update_frequency = int(update_freq_str) # Μετατροπή σε int                               
                            # Σε περίπτωση πρόκλησης εξαίρεσης η default τιμή ειναι 5.
                            except (ValueError, KeyError, AttributeError):
                                update_frequency = 5
                            # Συνθήκες Ενημέρωσης του Γραφήματος
                            update_conditions = (
                                iteration == 0 or # Στην 1η Επανάληψη
                                (iteration > 0 and iteration % update_frequency == 0) or # Κάθε Ν επαναλήψεις που έχει επιλέξει ο χρήστης στο Spinbox
                                (max_iterations > 0 and iteration == max_iterations-1 and iteration % update_frequency != 0) # Στην τελευταία Επανάληψη
                                )                            
                            # Αν οι συνθήκες ενημέρωσης ειναι True:
                            if update_conditions:
                                #print(f"DEBUG: Updating Convergence Curve at iteration {iteration} due to frequency {update_frequency}")
                                # Καλείται η μέθοδος update_convergence_plot() και σχεδιάζεται η Καμπύλης Σύγκλισης της Καταλληλότητας.
                                self.update_convergence_plot()

                    # Ενημέρωση Καμπυλών Χώρου Αναζήτησης.
                    elif msg_type == "spatial_plot_data":
                        # Αν είναι ενεργοποιημένο το toggle για την εμφάνιση των γραφημάτων.
                        if self.enable_spatial_live_update_var.get():
                            try:
                                # Ομοίως με προηγούμενως με την καμπύλη σύγκλισης
                                update_freq_str = self.parameters_dict["plot_update_freq"].get()
                                update_frequency = int(update_freq_str)                                                         
                            except (ValueError, KeyError, AttributeError):
                                update_frequency = 5
                            # Προσπαθεί να πάρει το value του key="iteration" απο το λεξικό αν δεν τα καταφέρει θα θέσιε την τιμή 0
                            iteration = msg_data.get("iteration",0) 

                            try:
                                max_iters_str = self.parameters_dict["max_iter"].get()
                                max_iterations_for_plot_check = int(max_iters_str)
                                if max_iterations_for_plot_check <= 0:
                                    max_iterations_for_plot_check = 1
                            except:
                                max_iterations_for_plot_check = 1
                            
                            # Συνθήκες Ενημέρωσης του Γραφήματος
                            update_conditions = (
                                iteration == 0 or # Στην 1η Επανάληψη
                                (iteration > 0 and iteration % update_frequency == 0) or # Κάθε Ν επαναλήψεις που έχει επιλέξει ο χρήστης στο Spinbox
                                (max_iterations > 0 and iteration == max_iterations-1 and iteration % update_frequency != 0) # Στην τελευταία Επανάληψη
                                )                            
                            # Αν οι συνθήκες ενημέρωσης ειναι True:
                            if update_conditions:
                                #print(f"DEBUG: Updating Spatial plot at iteration {iteration} due to frequency {update_frequency}")                           
                                
                                # Ελέγχουμε αν έχει δημιουργηθεί το widget notebook που θα φιλοξενήσει τις καρτέλες των γραφικών παραστάσεων
                                # αν δεν υπάρχει τότε συνεχίζουμε στην επόμενη επανάληψη του for για την κατανάλωση του επόμενου μυνήματος της ουράς.
                                if not hasattr(self, "plot_notebook") or self.plot_notebook is None:
                                    continue
                                try:
                                    # Αν υπάρχει ακόμα το Notebook και υπάρχει ενεργή καρτέλα τότε:
                                    if self.plot_notebook.winfo_exists() and self.plot_notebook.select():
                                        # Λαμβάνουμε το Index του στοχείου της λίστας που αντιστοιχεί στο λεξικό με τις ρυθμίσεις της επιλεγμένης ενεργής καρτέλας
                                        current_tab_index = self.plot_notebook.index(self.plot_notebook.select())
                                        # Λαμβάνουμε το κλειδί απο μία λίστα που περιέχει λεξικά 
                                        # με ρυθμίσεις για τα τρία γραφήματα και άρα για τις 3 καρτέλες
                                        active_tab_key = self.plot_configs_list[current_tab_index]["key"]
                                    else:
                                        active_tab_key = None
                                except(tk.TclError, IndexError, AttributeError):
                                    active_tab_key = None

                                if active_tab_key == "3d_view":
                                    #print(f"DEBUG: Updating 3D Plot at iteration: {iteration}.")
                                    self.update_3d_plot_content(msg_data)

                                elif active_tab_key == "top_view":
                                    #print(f"DEBUG: Updating Top View Plot at iteration: {iteration}.")
                                    self.update_top_view_plot_content(msg_data)                                        
                
                    elif msg_type == "run_completed_stats":
                        run_exec_time = msg_data.get("gwo_time", 0.0)
                        if isinstance(run_exec_time, (int, float)):
                            # Σωρεύουμε τον χρόνο εκτέλεσης του κάθε RUN σε μία μεταβλητή σωρευτή
                            self.cumulative_execution_time += run_exec_time

                        time_text_value = f"{self.cumulative_execution_time:.4f}"
                        # Ενημερώνουμε το Label του Χρόνου για να ενημερωθεί ο Χρήστης.                    
                        self.exec_time_label.config(text=time_text_value)                  
                    
                    # Αν το μύνημα είναι τύπου "all_runs_finished", το οποίο στέλνεται οταν ολοκληρωθεί η εκτέλεση του αλγορίθμου
                    # ή ο χρήστης έχει πατήσει το κουμπί STOP τότε:
                    elif msg_type == "all_runs_finished":                    
                        # Όλα τα runs ολοκληρώθηκαν ή σταμάτησαν
                        self.log_message("--- All GWO RUNS completed or stopped. ---")                    
                        # Ενεργοποιούμε και απενεργοποιούμε τα κουμπιά αναλόγως
                        self.run_button.config(state=NORMAL)
                        self.stop_button.config(state=DISABLED)
                        self.progress_bar['value'] = 100
                        # Αποθηκεύουμε τα δεδομένα του τελευταίου RUN του αλγορίθμου
                        final_results_data = msg_data

                        # Τελική ενημέρωση του γραφήματος σύγκλισης
                        if self.enable_convergence_plot_var.get():
                            #print("DEBUG: Final update for convergence plot.")
                            self.update_convergence_plot()
                        # Τελική ενημέρωση των γραφημάτων 3D ή Top View αναλόγως της ενεργής καρτέλας.
                        #if self.enable_spatial_live_update_var.get() and final_results_data:
                            #print("DEBUG: Attempting final update for active spatial plot.")
                            #self.update_3d_plot_content(msg_data)
                            #self.update_top_view_plot_content(msg_data)                              
        except Exception as e:
            # Εμφανίζουμε τυχόν λάθη που προέκυψαν κατά την επεξεργασία
            self.log_message(f"Error processing GUI queue: {e}")
        finally:
            # Η επόμενη κλήση της μεθόδου θα γίνει σε 100msec προκειμένου να ελέγχουμε 
            # συνέχεια για τυχόν νέα μυνήματα απο το νήμα του GWO.
            self.after(100, self.process_gui_queue)        


    def gui_callback_from_thread(self, msg_type, data):
        """
         Η συνάρτηση στέλνει μηνύματα απο το νήμα εκτέλεσης του GWO στο νήμα του GUI 
         με χρήση μιας thread safe ουρας για να αποφύγουμε race conditions μεταξύ των δύο νημάτων.   

        Args:
            msg_type (str): τύπος μηνύματος (π.χ. "log").
            data (any): Δεδομένα μηνύματος.
        """
        self.gui_queue.put((msg_type, data))

    def stop_gwo(self):
        """
            Η συνάρτηση στέλνει σήμα διακοπής στον αλγόριθμο GWO και απενεργοποιεί το κουμπί Stop.
        """    
        # Αν το thread του GWO τρέχει:
        if self.gwo_thread and self.gwo_thread.is_alive():
            self.log_message("--- Stop signal sent. Waiting for current GWO operations to complete... ---")        
            # το stop_event γίνεται True, η εκτέλεση του αλγορίθμου θα διακοπεί.
            self.stop_event.set()        
            # Απενεργοποιούμε το κουμπί STOP
            self.stop_button.config(state=DISABLED)


    #7. Utility Μέθοδοι GUI ===================================================================================

    def log_message(self, message):
        """
            Εμφανίζει ένα μύνημα στο text widget στο Log_frame.

            Args:
                message(str): Το μήνυμα που θα εμφανιστεί στο log.

        """        
        # Ξεκλειδώνουμε προσωρινά το Text widget.
        self.log_text.config(state=NORMAL)
        # Προσθέτουμε το μήνυμα.
        self.log_text.insert(END, str(message) + "\n")
        # Αυτόματη κύλιση προς τα κάτω για να φαίνεται το τελευταίο μήνυμα.
        self.log_text.see(END)
        # Κλειδώνουμε ξανά για να μην μπορεί να το επεξεργαστεί ο χρήστης.
        self.log_text.config(state=DISABLED)
        # Γρήγορη ανανέωση για να φανεί το μήνυμα.
        self.update_idletasks()

    # 8. Μέθοδος Χειρισμού Κλεισίματος Παραθύρου ==============================================================

    def on_closing(self):
        """
            Η συνάρτηση χειρίζεται το κλείσιμο του παραθύρου της εφαρμογής.
            Αν ο GWO τρέχει τότε προσπαθεί θα προσπαθήσει πρώτα να τον σταματήσει,
            εν συνεχεία κλείνει όλα τα γραφήματα Matplotlib και κλείνει το κυρίως παράθυρο της εφαρμογής.
        """
        # Ελέγχουμε αν το νήμα του GWO υπάρχει και είναι ενεργό.
        if self.gwo_thread and self.gwo_thread.is_alive():
            self.log_message("Window closing: Attempting to stop GWO thread...")
            # Θέτουμε το stop_event σε True για να διακοπεί η εκτέλεση του GWO.
            self.stop_event.set()            
            # Περιμένουμε για 1 sec να σταματήσει το thread και να επιστρέψει τυχόν αποτελέσματα.
            self.gwo_thread.join(timeout=1.0)
            # Αν το νήμα τρέχει ακόμα ενημερώνουμε τον χρήστη με ένα μύνημα
            if self.gwo_thread.is_alive():
                self.log_message("Warning: GWO thread still running...")
        
        # Κλείνουμε τα παράθυρα όλων των γραφημάτων.
        plt.close("all")       
        # Κλείνουμε το παράθυρο της εφαρμογής.
        self.destroy()
               

if __name__ == "__main__":
    # Διασφαλίζουμε ότι το Matplotlib θα συνεργαστεί σωστά με το Tkinter
    plt.switch_backend('TkAgg')    
    app = GWOApp()    
    app.mainloop()