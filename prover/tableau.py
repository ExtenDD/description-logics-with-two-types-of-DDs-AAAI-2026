import forms
import rules
import interpretation

import re
import time
from copy import deepcopy


class DL_Tableau:
    """Class for tableau"""
    
    #initialize the intepretation with input containing concepts, ABox, RBox and TBox    
    def __init__(self,
                 concept = None,
                 ABox = None, 
                 RBox = None,
                 TBox = None):
        
        self.interpretation = interpretation.Interpretation()  #we initialize the interpretation object
        world_names_str = set()   #set of strings containing world names - a working variable
        self.time_out = False     #attribute that stores the information, if creating the tableau using a function "build_tableu" took more time than the defined limit
        

        #1. ABox argument-----
        
        if ABox == None:
            pass
        elif not isinstance(ABox, dict):
            raise TypeError("ABox argument was not properly introduced. Please use Python dictionary syntax, with keys corresponding to individuals and values corresponding to a concept or list of concepts")
        else:    
            for world, formulas in ABox.items():
                
                world = world.replace(" ", "")   #white spaces have to be removed

                if bool(re.match(r"i.[A-Z]\w*", world)): #if the world is a local description in the form of the world name, we automatically pass the local description formula to the formula list
                    if isinstance(formulas,list):
                        formulas.append(world) 
                    elif isinstance(formulas,str):
                        formulas = [world] + [formulas]

                #parsing    
                if isinstance(formulas, str):
                    parser_tree = forms.parser_DL.parse(formulas)
                    fml_parsed = forms.ToFml().transform(parser_tree)
                    fmls_parsed = [fml_parsed]
                elif isinstance(formulas, list):
                    fmls_parsed = []
                    for fml in formulas:
                        parser_tree = forms.parser_DL.parse(fml)
                        fml_parsed = forms.ToFml().transform(parser_tree)
                        fmls_parsed.append(fml_parsed)
                locals()[world] = x = self.interpretation.add_world(fmls_parsed)
                x._world_name_str = world
                world_names_str.update(set(ABox.keys()))

              
            
        #2. RBox argument --
      
        if RBox == None:
            pass
        elif not isinstance(RBox, dict):
            raise TypeError("RBox argument was not properly introduced. Please use Python dictionary syntax, with keys corresponding to relations (roles) and values corresponding to lists, with each of its elements being a list of two related worlds (individuals)")
        else:
            for role, pairs_of_worlds in RBox.items():

                role = role.replace(" ", "")   #white spaces have to be removed

                #if the first argument (pair of worlds) is of the form ['w1','w2'] we have to trasform it into [['w1','w2']] for the rest of the code to work properly
                if isinstance(pairs_of_worlds, list) and len(pairs_of_worlds)==2 and isinstance(pairs_of_worlds[0],str):
                    y = list()
                    y.append(pairs_of_worlds)
                    pairs_of_worlds=y

                if not isinstance(pairs_of_worlds, list):
                    raise TypeError("Please insert the information about related worlds as lists of lists of pairs of worlds")  #ERROR!!!!!
                else:
                    for pair in pairs_of_worlds:
                        if not (isinstance(pair, list) and len(pair)==2 and isinstance(pair[0],str) and isinstance(pair[1],str)):
                            raise TypeError("Each pair of worlds should be a separate list composed of two strings") #ERROR

                        pair[0] = pair[0].replace(" ", "")   #white spaces have to be removed
                        pair[1] = pair[1].replace(" ", "")   #white spaces have to be removed
                        
                         
                        for i in (0,1):
                            if not pair[i] in world_names_str: #check if the world has already been created in ABox
                                if bool(re.match(r"i.[A-Z]\w*", pair[i])): #if the world is a local description in the form of the world name, we automatically pass the local description formula to the formula list
                                    parser_tree = forms.parser_DL.parse(pair[i])
                                    fml_parsed = forms.ToFml().transform(parser_tree)
                                    locals()[pair[i]] = x = self.interpretation.add_world([fml_parsed]) 
                                else:
                                    locals()[pair[i]] = x = self.interpretation.add_world([])
                                x._world_name_str = pair[i]
                                world_names_str.update({pair[i]})

                        self.interpretation.add_edge(locals()[pair[0]],locals()[pair[1]], role)    
        
        
        
        #3. concept argument --
        
        #create a concept object
        if concept == None:
            pass
        elif isinstance(concept, str):
            parser_tree = forms.parser_DL.parse(concept)
            fml_parsed = forms.ToFml().transform(parser_tree)
            fmls_parsed = [fml_parsed]
        elif isinstance(concept, list):
            fmls_parsed = []
            for fml in concept:
                parser_tree = forms.parser_DL.parse(fml)
                fml_parsed = forms.ToFml().transform(parser_tree)
                fmls_parsed.append(fml_parsed)
        else:
            raise TypeError("Please insert a correctly built concept or list of concepts in the argument 'concept'")


        #name the world "w0"; if this name already appearad in ABox or RBox, choose the first availabe from: {"w00", "w000",...}
        if not 'w0' in world_names_str:
            base_world_name = 'w0'
        else:
            for i in range(2, len(world_names_str) + 2):
                if 'w'+i*'0' in world_names_str:
                    continue
                
                base_world_name = 'w'+i*'0'
                break

        
        #add the concepts from the argument "concept" to the interpetation
        if concept != None:
            locals()[base_world_name] = x = self.interpretation.add_world(fmls_parsed)
            x._world_name_str = base_world_name
            world_names_str.update({base_world_name}) 
        
        
            
        #4. TBox argument  --
        
        if TBox == None:
            pass
        else:
            if isinstance(TBox, str):
                parser_tree = forms.parser_DL.parse(TBox)
                fml_parsed = forms.ToFml().transform(parser_tree)
                if not isinstance(fml_parsed, forms.Conditional): 
                    raise TypeError("Please enter only subsumptions in the TBox!")
                fmls_parsed = [fml_parsed]
            elif isinstance(TBox, list):
                fmls_parsed = []
                for fml in TBox:
                    parser_tree = forms.parser_DL.parse(fml)
                    fml_parsed = forms.ToFml().transform(parser_tree)
                    if not isinstance(fml_parsed, forms.Conditional):#ERROR!!!!!
                        print("Please enter only conditionals in the TBox!")                    
                    fmls_parsed.append(fml_parsed)
            else:
                print("Please insert a subsumption or a list of subsumptions in the TBox")
                    
            #we're applying the TBox rule - changing implications to negation of conjunction
            fmls_parsed = [forms.Negation(forms.Conjunction(fml.subs[0], forms.Negation(fml.subs[1]))) for fml in fmls_parsed]
                
            #adding the parsed formulas to all the worlds
            if len(self.interpretation.worlds())>0:
                for w in self.interpretation.worlds():
                    w._formulas = w._formulas + fmls_parsed 
            else: #that's when the TBox is the only "source of worlds"
                self.w0 = self.interpretation.add_world(fmls_parsed) #world label
                self.w0._world_name_str = "w0"
                world_names_str.update({"w0"})           

            self.interpretation.TBox_formulas = set(fmls_parsed)  #saving the TBox (parsed and converted to neg. conjuction) formulas for later (will be placed in every newly created world)
            
        #store the world names in an attribute of the interpretation
        self.interpretation._world_names_str = world_names_str


        #creating a set of all atom symbols occurring in the interpretation        
        self.interpretation._all_atoms_in_interpretation = set()

        #keeping the initial interpretation (before applying any rules)
        self.initial_interpretation = deepcopy(self.interpretation)  
        
        
        
        
        ##################################################################
        #5. Solver - we build the tableau ----------------------------------
        #this is the main function to apply on the DL_Tableau object

    def build_tableau(self):
        """Build the tableau by applying the rules from the script "rules".
        
        Argument: the tableau object
        
        Output: a tuple consisting of four objects:
            [0]: True, if the formula is a time-out, False otherwise
            [1]: True, if the formula is satisfiable, False otherwise
            [2]: Number of closed branches
            [3]: Number of applied rules
        """
        


        #initializing a list of all "alternative" interpretations to be explored on branches of the tableau         
        alternative_interpretations = []
                
        #list of rules to applied; the rules will be applied in the order defined in this list
        rules_to_apply = [rules.clash_rule,
                          rules.double_neg_rule,
                          rules.conjunction_rule,
                          rules.role_rule_2,
                          rules.negated_conjunction_rule,
                          rules.local_description_rule_1,
                          rules.local_description_rule_2,
                          rules.local_description_rule_3,
                          rules.local_description_cut_rule,
                          rules.global_description_rule_1,
                          rules.global_description_rule_2,
                          rules.global_description_rule_3,
                          rules.global_description_cut_rule,
                          rules.role_rule_1]
        
        rules_to_apply = tuple(rules_to_apply)

        no_rules_to_apply = len(rules_to_apply)
        
        #initializing the counter of applied rules
        self.no_rules_applied = 0 
        
        #initializing the variable storing the satifiability status
        self.is_satisfiable = None

        #initializing the counter of closed branches of the tableau (in which an inconsistency has been found)        
        self.closed_branches_count = 0
        
        #division of formulas in the formula list in each world of the interpretation into sets of subtypes of formulas
        #note - the attribute "_formulas" of each world will be a dictionary, composed of sets of formulas as values from now on (not a list, as it was the case in the input)
        for w in self.interpretation.worlds():
            
            new_fml_posit = set()
            new_fml_negat = set()
            
            for fml in w._formulas:
                if isinstance(fml, forms.Negation):
                    new_fml_negat.update({fml})
                else:
                    new_fml_posit.update({fml})                        

            w._formulas = {'atoms': set(),
                           'neg_atoms': set(),
                           'double_neg': set(),
                           'conjunction': set(),
                           'neg_conjunction': set(),
                           'diamond': set(),
                           'neg_diamond': set(),
                           'global_desc': set(),
                           'neg_global_desc': set(),
                           'local_desc': set(),
                           'neg_local_desc': set(),
                           'proc_posit': set(),
                           'proc_negat': set(),
                           'proc_global_desc': set(),
                           'proc_local_desc': set(),
                           'new_fml_posit': new_fml_posit,
                           'new_fml_negat': new_fml_negat}

            del new_fml_negat, new_fml_posit

        #start measuring the time in order to stop proceeding if the prover works too long (if a given time litmit has been crossed; the limit is given below in the while loop)
        start_time = time.time()

        #initialize the iterator of rules
        rules_iterator = 0


        while rules_iterator < no_rules_to_apply:

            #here we set the time limit; if it is exceeded, formula is considered a time-out 
            if time.time() - start_time > 12:
                self.time_out = True
                break
            
            #reset the iterator after any rule has been applied
            rules_iterator = 0

            for rule in rules_to_apply:  #iterate over the rules 
                
                #results of applying the rule: interpretation, True/False, True/False, list of alternative interpretations (possibly empty)
                new_interpretation, inconsistency_found, rule_applied, new_alt_interpretations = rule(self.interpretation)  
                
                if inconsistency_found:
                    self.closed_branches_count += 1
                    self.no_rules_applied += 1
                    
                    if len(alternative_interpretations) == 0: #no more "alternative interpretations" - stop building the tableau - it is not satisfiable
                        self.is_satisfiable = False
                        break
                    else:
                        self.interpretation = alternative_interpretations.pop() #pick the first available interpretation from a list, if a branch has been closed
                        break

                elif rule_applied: #rule has been applied
                    self.interpretation = new_interpretation
                    self.no_rules_applied += 1
                    alternative_interpretations.extend(new_alt_interpretations)  #add new "alternative interpretations" to the list - if there are any to add
                    break  
                else:
                    rules_iterator += 1    #rule has not been applied
                        
            if self.is_satisfiable == False:
                break  #out of the whole while loop


        #if there are no more rules to apply and the formula is not a time out - it is satisfiable 
        if self.is_satisfiable is None and self.time_out is False and rules_iterator == no_rules_to_apply:
            self.is_satisfiable = True



        #PRINT OUT OF THE INTERPRETATION
        #note - the interpretation should not be considered as a proper model! 
        #print world(individual) names and formulas satisfied in the worlds
        for w in self.interpretation.worlds():
            
            print(f"Individual name: {w._world_name_str} \n Concepts:")
            for fml in set.union(*w._formulas.values()):
                print("  ", fml)  #print the formulas in "nice" looking form
            print("\n")

        #print relations between worlds
        for v1, w  in self.interpretation._outgoing.items():
            if bool(w): #don't take into account worlds with no outging edges (bool(w) = dictionary w is not empty)
                for v2, mod_types in w.items():
                    for mod_type in mod_types:
                        print(f"Role type: {mod_type} \n Origin individual: {v1._world_name_str} \n Destination individual: {v2._world_name_str} \n")

        if self.is_satisfiable:
            print("Input is satisfiable")
        elif not self.is_satisfiable:
            print("Input is not satisfiable")
        elif self.is_satisfiable == None and self.time_out:
            print("Time-out limit reached - no information about satisfiability")             
            
        return(self.time_out, self.is_satisfiable, self.closed_branches_count, self.no_rules_applied)
    



    def print_initial_interpretation(self):
        """print ""initial"" interpretation (before applying the rules) in a text form"""
        #note - the interpretation should not be considered as a proper model 

        #print world names and formulas satisfied in the worlds
        for w in self.initial_interpretation.worlds():
            
            print(f"Individual name: {w._world_name_str} \n Concepts:")
            for fml in w._formulas:
                print("  ", fml)  #print the formulas in "nice" looking form
            print("\n")

        #print relations between worlds       
        for v1, w  in self.initial_interpretation._outgoing.items():
            if bool(w): #don't take into account worlds with no outging edges (bool(w) = dictionary w is not empty)
                for v2, mod_types in w.items():
                    for mod_type in mod_types:
                        print(f"Role type: {mod_type} \n Origin individual: {v1._world_name_str} \n Destination individual: {v2._world_name_str} \n")





