import forms
from copy import deepcopy
import generators


def relocate_to_new_fml_sets(formulas_dict, new_fml):
    """ Place each new formula, that appeared in a given world as a result of applying a rule, in one of the subsets: 
    "new_fml_posit" of "new_fml_negat" - depending on whether it is a negation. This is done to limit applygin the 
    clash rule to comparing those new formulas to all the others, already present in the world before applyting the 
    rule (this way we avoid repeating the same checks in the clash rule all over again)

    Arguments: 
        new_fml: a new formula, that appears in the world as an effect of applying a given rule    
        formulas_dict: an object of the form "w._formulas", where "w" is the world in which the new formula appears
            and "_formulas" is its attribute containing the dictionary of formulas
    
    """
    if isinstance(new_fml, forms.Negation):
        formulas_dict['new_fml_negat'].update({new_fml}) 
    else:
        formulas_dict['new_fml_posit'].update({new_fml}) 



"""
All the functions below implement rules of the calculus TAB(ALCi). Each function takes an interpretation as an 
argument, and outpus 4 elements:

[0] the modified interpretation (Intepretation object)
[1] True if inconsistency was found (can happen only for the Clash rule), False otherwise
[2] True if the rule has been applied, False otherwise
[3] list of "alternative interpretations" that correspond to new branches of the tableau; for deterministic rules, this list is empty
    
"""




#CLASH RULE -------------------------------------------------


def clash_rule(interpretation):
    """ Function implementing the Clash rule"""
    
    for w in interpretation.worlds():
        
        #number of new formulas
        no_new_fmls = len(w._formulas['new_fml_posit'] | w._formulas['new_fml_negat'])

        if no_new_fmls == 0:
            continue #no new formulas, pass to the next world        

        else:
            if no_new_fmls>1:   #check for consistency among the new formulas         
                fml_pairs_generator = ((new_posit_fml, new_negat_fml) for new_posit_fml in w._formulas['new_fml_posit'] for new_negat_fml in w._formulas['new_fml_negat'])         
    
                for pair in fml_pairs_generator:
                    if pair[0] == pair[1].sub:
                        return(interpretation, True, True, [])
            
            #positive new formulas vs negative formulas
            fml_pairs_generator = ((new_posit_fml, neg_fml) for new_posit_fml in w._formulas['new_fml_posit'] for neg_fml in (w._formulas['neg_atoms'] | w._formulas['neg_conjunction'] | w._formulas['neg_diamond'] | w._formulas['neg_global_desc'] | w._formulas['neg_local_desc'] | w._formulas['proc_negat']) )        

            for pair in fml_pairs_generator:
                if pair[0] == pair[1].sub:
                    return(interpretation, True, True, [])
                
            #negative new formulas vs positive formulas            
            fml_pairs_generator = ((new_negat_fml, pos_fml) for new_negat_fml in w._formulas['new_fml_negat']  for pos_fml in (w._formulas['atoms'] | w._formulas['conjunction'] | w._formulas['diamond'] | w._formulas['global_desc'] | w._formulas['local_desc'] | w._formulas['proc_posit'] | w._formulas['proc_global_desc'] | w._formulas['proc_local_desc']) )  

            for pair in fml_pairs_generator:
                if pair[0].sub == pair[1]:
                    return(interpretation, True, True, [])
            
            for new_fml in w._formulas['new_fml_negat']:
                if isinstance(new_fml.sub, forms.Negation):
                    w._formulas['double_neg'].update({new_fml}) 
                elif isinstance(new_fml.sub, forms.Atom):
                    w._formulas['neg_atoms'].update({new_fml}) 
                elif isinstance(new_fml.sub, forms.Conjunction):
                    w._formulas['neg_conjunction'].update({new_fml})
                elif isinstance(new_fml.sub, forms.Diamond):
                    w._formulas['neg_diamond'].update({new_fml})              
                elif isinstance(new_fml.sub, forms.Description_Global):
                    w._formulas['neg_global_desc'].update({new_fml})              
                elif isinstance(new_fml.sub, forms.Description_Local):
                    w._formulas['neg_local_desc'].update({new_fml})              
                        
            for new_fml in w._formulas['new_fml_posit']:                
                if isinstance(new_fml, forms.Atom):
                    w._formulas['atoms'].update({new_fml}) 
                elif isinstance(new_fml, forms.Conjunction):
                    w._formulas['conjunction'].update({new_fml}) 
                elif isinstance(new_fml, forms.Diamond):
                    w._formulas['diamond'].update({new_fml})              
                elif isinstance(new_fml, forms.Description_Global):
                    w._formulas['global_desc'].update({new_fml})              
                elif isinstance(new_fml, forms.Description_Local):
                    w._formulas['local_desc'].update({new_fml})              

            w._formulas['new_fml_negat'] = set()
            w._formulas['new_fml_posit'] = set()


    return (interpretation, False, False, [])            



#RULE DOUBLE NEGATION ----------------------------


def double_neg_rule(interpretation):
    """ Function implementing the propositional rule for double negation"""


    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['double_neg'])

        for fml in fml_set_copy:        

            if fml.sub.sub in set.union(*w._formulas.values()):
                w._formulas['double_neg'].remove(fml) 
                w._formulas['proc_negat'].update({fml}) 
                continue
            else:
                relocate_to_new_fml_sets(w._formulas, fml.sub.sub)
                w._formulas['double_neg'].remove(fml) 
                w._formulas['proc_negat'].update({fml}) 
        
            return(interpretation, False, True, [])
            
    return(interpretation, False, False, [])




#RULE CONJUNCTION ----------------------------

def conjunction_rule(interpretation):
    """ Function implementing the propositional rule for conjunction"""
    
    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['conjunction'])

        for fml in fml_set_copy:        


            v0 = fml.subs[0] in set.union(*w._formulas.values())
            v1 = fml.subs[1] in set.union(*w._formulas.values())

            if v0 and v1:
                w._formulas['conjunction'].remove(fml) 
                w._formulas['proc_posit'].update({fml}) 
                continue
            
            
            if not v0:
                relocate_to_new_fml_sets(w._formulas, fml.subs[0])
                
            if not v1:
                relocate_to_new_fml_sets(w._formulas, fml.subs[1])

            w._formulas['conjunction'].remove(fml) 
            w._formulas['proc_posit'].update({fml}) 


            return(interpretation, False, True, [])

    return(interpretation, False, False, [])



#RULE NEGATED CONJUNCTION ----------------------------


def negated_conjunction_rule(interpretation):
    """ Function implementing the propositional rule for conjunction"""

    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['neg_conjunction'])

        for fml in fml_set_copy:        

            if (forms.Negation(fml.sub.subs[0]) in set.union(*w._formulas.values())) or (forms.Negation(fml.sub.subs[1]) in set.union(*w._formulas.values())):

                continue #to the next formula
            else:
                alt_interpretation = deepcopy(interpretation)

                relocate_to_new_fml_sets(w._formulas, forms.Negation(fml.sub.subs[0]))
            
                w._formulas['neg_conjunction'].remove(fml) 
                w._formulas['proc_negat'].update({fml}) 
            
                for w_alt in alt_interpretation.worlds():
                    if w_alt._world_name_str == w._world_name_str:
                        relocate_to_new_fml_sets(w_alt._formulas, forms.Negation(fml.sub.subs[1]))
                        w_alt._formulas['neg_conjunction'].remove(fml) 
                        w_alt._formulas['proc_negat'].update({fml}) 
                        
                return(interpretation, False, True, [alt_interpretation])

    return(interpretation, False, False, [])                   




# ROLE RULE 1  ----------------------------


def role_rule_1(interpretation):
    """ Function implementing the role rule for "Ǝr" """
    
    for w in interpretation.worlds():

        cand_blocking_new = {}        

        #updating the list of 'candidate worlds' and (within it) - blocked diamond formulas 
        if bool(w._candidates_blocking) and bool(w._box_subformulas):
            for cand_world, roles_dict in w._candidates_blocking.items():
                cand_blocking_new[cand_world] = {}
                for role, blocked_forms  in roles_dict.items():
                    cand_blocking_new[cand_world][role] = blocked_forms
                    if role in w._box_subformulas.keys():
                        if w._box_subformulas[role] <= set.union(*cand_world._formulas.values()): #if for all formulas X such that box(X) are in world w, X is in the candidate world
                            pass 
                        else:
                            for bfml in blocked_forms: #the blocked formula is removed from the 'processed' set - it will have to be analysed again
                                w._formulas['proc_posit'].remove(bfml) 
                                w._formulas['diamond'].update({bfml})
                            
                            del cand_blocking_new[cand_world][role] 
                
                if not bool(cand_blocking_new[cand_world]):
                    del cand_blocking_new[cand_world]
                          
                            
        w._candidates_blocking = cand_blocking_new
        
        fml_set_copy = list(w._formulas['diamond'])

        for fml in fml_set_copy:        

            
            #Options 1 and 2 implement the blocking mechanism described in the paper

            #Option1 - looking for a related world
            rel_worlds_list = interpretation.related_worlds(w, fml.role) #list of worlds related with w by role indicated in the "diamond" formula
            if len(rel_worlds_list)>0:   #if any world is related to w, with the relation role  
               if any({fml.sub2 in set.union(*rel_w._formulas.values()) for rel_w in rel_worlds_list}): #does any of the related worlds contain the formula indicated in the "diamond" formula?
                  
                   #mark the analysed formula fml as processed
                   w._formulas['diamond'].remove(fml) 
                   w._formulas['proc_posit'].update({fml}) 

                   return(interpretation, False, True, []) #rule applied, exit
                  
           
            #Option 2 - looking for a "candidate world"
            for unrel_v in interpretation.unrelated_worlds(w, fml.role): 
                if (fml.sub2 in set.union(*unrel_v._formulas.values())) and (fml.role not in w._box_subformulas.keys() or w._box_subformulas[fml.role] <= set.union(*unrel_v._formulas.values())):
                    if unrel_v in w._candidates_blocking.keys():
                        w._candidates_blocking[unrel_v][fml.role].update({fml})
                    else:
                        w._candidates_blocking[unrel_v] = {fml.role: {fml}}

                    w._formulas['diamond'].remove(fml) 
                    w._formulas['proc_posit'].update({fml}) 

                    return(interpretation, False, True, [])


                               
            #Option3 - creating new world (this option directly applies the rule, if the "candidate" world has not been found)
            new_world = interpretation.add_world({'atoms': set(),
                                                  'neg_atoms': set(),
                                                  'double_neg': set(),
                                                  'conjunction': set(),
                                                  'neg_conjunction': interpretation.TBox_formulas,
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
                                                  'new_fml_posit': set(),
                                                  'new_fml_negat': set()})
    
            new_world._world_name_str = generators.new_world_name(interpretation)
           
            #place the formula in the new world
            relocate_to_new_fml_sets(new_world._formulas, fml.sub2)                

            interpretation.add_edge(w, new_world, fml.role)    

            #moving concepts ~X, such that ~*E (role) X to the new world
            for box_fml in w._formulas['proc_negat']:
                if isinstance(box_fml.sub, forms.Diamond) and (box_fml.sub.role == fml.role):
                    relocate_to_new_fml_sets(new_world._formulas, forms.Negation(box_fml.sub.sub2))
                                             
            del new_world 
           
            return(interpretation, False, True, [])

    return(interpretation, False, False, [])                   




# ROLE RULE 2  ----------------------------


def role_rule_2(interpretation):
    """ Function implementing the role rule for "~Ǝr" """
    
    
    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['neg_diamond'])

        for fml in fml_set_copy:        

                #updating the list of concepts X, such that ~*E role X is a concept
            if fml.sub.role in w._box_subformulas.keys():
                w._box_subformulas[fml.sub.role].update({fml})
            else:
                w._box_subformulas[fml.sub.role] = {fml}
            
            
            #add the formula to all the related worlds                
            for v in interpretation.related_worlds(w, fml.sub.role):
                relocate_to_new_fml_sets(v._formulas, forms.Negation(fml.sub.sub2))

            w._formulas['neg_diamond'].remove(fml) 
            w._formulas['proc_negat'].update({fml})  
                                 
            return(interpretation, False, True, [])
    
    return(interpretation, False, False, [])                   
                                    



# GLOBAL DESCRIPTION RULE 1  ----------------------------


def global_description_rule_1(interpretation):
    """ Function implementing the first rule for global descriptions: i(g,1) """

    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['global_desc'])

        for fml in fml_set_copy:        

            continue_to_next_formula = False #working variable for Option 1 below           

            #Option 1 - are both formulas in the description satisfied in some world?
            for v in interpretation.worlds():
                if {fml.subs[0], fml.subs[1]} <= set.union(*v._formulas.values()):
                    w._formulas['global_desc'].remove(fml) 
                    w._formulas['proc_global_desc'].update({fml})  
                    continue_to_next_formula = True
                    break


            #if Option 1 applied - continue to next formula            
            if continue_to_next_formula:
                continue



            #Option 2 - is the first formula in the description satisfied in some world?                    
            for v in interpretation.worlds():
                if fml.subs[0] in set.union(*v._formulas.values()):
                    relocate_to_new_fml_sets(v._formulas, fml.subs[1])

                    w._formulas['global_desc'].remove(fml) 
                    w._formulas['proc_global_desc'].update({fml})  
                    
                    return(interpretation, False, True, [])


            #Option 3 - else - add a new world with both formulas from the description

            new_world = interpretation.add_world({'atoms': set(),
                                                  'neg_atoms': set(),
                                                  'double_neg': set(),
                                                  'conjunction': set(),
                                                  'neg_conjunction': interpretation.TBox_formulas,
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
                                                  'new_fml_posit': set(),
                                                  'new_fml_negat': set()})
            
            new_world._world_name_str = generators.new_world_name(interpretation)

            relocate_to_new_fml_sets(new_world._formulas, fml.subs[0])
            relocate_to_new_fml_sets(new_world._formulas, fml.subs[1])

            w._formulas['global_desc'].remove(fml) 
            w._formulas['proc_global_desc'].update({fml})  
            
            del new_world            

            return(interpretation, False, True, [])

    return(interpretation, False, False, [])                   



# GLOBAL DESCRIPTION RULE 2  ----------------------------


def global_description_rule_2(interpretation):
    """ Function implementing the second rule for global descriptions: i(g,2) """

    forms_checked = set()
    
    for w in interpretation.worlds():

        #here we need to iterate over all formulas, to make sure each formula in each world is checked, before "rule not applied" is returned
        for fml in (w._formulas['global_desc'] | w._formulas['proc_global_desc']):
        #in case of this rule, we consider both processed and unprocessed formulas, and do not modify any of them in course of applying the rule

            if fml.subs[0] in forms_checked:
                continue

            worlds_to_be_unified_names = set()
            worlds_to_be_unified_world_copies = list()

            #create working copies of the worlds to be unified            
            for v in interpretation.worlds():
                if fml.subs[0] in set.union(*v._formulas.values()):
                    worlds_to_be_unified_names.update({v._world_name_str})
                    worlds_to_be_unified_world_copies.append(v)
            
            if len(worlds_to_be_unified_names) < 2:
                continue #to the next formula - rule not applied
            elif all([set.union(*z._formulas.values())==set.union(*worlds_to_be_unified_world_copies[0]._formulas.values()) for z in worlds_to_be_unified_world_copies[1:]]):
                forms_checked.update({fml.subs[0]})
                continue #to the next formula - rule not applied (all the worlds have the same sets of formulas)
            else:
                formulas_sum = set.union(*[set.union(*z._formulas.values()) for z in worlds_to_be_unified_world_copies])

                for v in interpretation.worlds():
                    if v._world_name_str in worlds_to_be_unified_names:
                        for form in formulas_sum - set.union(*v._formulas.values()):
                            relocate_to_new_fml_sets(v._formulas, form)


                del worlds_to_be_unified_names
                del worlds_to_be_unified_world_copies
                
                
                return(interpretation, False, True, [])
                
    return(interpretation, False, False, [])
                    


# GLOBAL DESCRIPTION RULE 3  ----------------------------


def global_description_rule_3(interpretation):
    """ Function implementing the rule for negated global descriptions: ~i(g) """

    
    for w in interpretation.worlds():
        
        #removing from the set 'neg_global_desc' such formulas ~@ A X that A is an appropriate set (of formulas A such that Option 3 of GD RULE 3 has already been applied to ~@ A X)
        neg_GD_forms_to_remove = {fml for fml in w._formulas['neg_global_desc'] if fml.sub.subs[0] in interpretation._GlDesc_rule3_fml_set}
        w._formulas['neg_global_desc'].difference_update(neg_GD_forms_to_remove) 
        w._formulas['proc_negat'].update(neg_GD_forms_to_remove) 
        del neg_GD_forms_to_remove


        for fml in w._formulas['neg_global_desc']:

            for v in interpretation.worlds():
                if forms.Negation(fml.sub.subs[0]) in set.union(*v._formulas.values()) or forms.Negation(fml.sub.subs[1]) in set.union(*v._formulas.values()):
                    continue #pass to the next world v
                else:
                    alt_interpretation1 = deepcopy(interpretation)
                    alt_interpretation2 = deepcopy(interpretation)
                    
                    #1. updating current interpretation --
                    relocate_to_new_fml_sets(v._formulas, forms.Negation(fml.sub.subs[0]))


                    #2. updating the "alternative interpretation 1" --
                    for w_alt in alt_interpretation1.worlds():
                        if w_alt._world_name_str == v._world_name_str:
                            relocate_to_new_fml_sets(w_alt._formulas, forms.Negation(fml.sub.subs[1]))
           
           
                    #3. updating the "alternative interpretation 2" --
           
                    fresh_atom_str = generators.new_fresh_atom(alt_interpretation2)
                    parser_tree = forms.parser_DL.parse(fresh_atom_str)
                    fresh_atom = forms.ToFml().transform(parser_tree)


                    #first new world
                    new_world = alt_interpretation2.add_world({'atoms': set(),
                                                               'neg_atoms': set(),
                                                               'double_neg': set(),
                                                               'conjunction': set(),
                                                               'neg_conjunction': interpretation.TBox_formulas,
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
                                                               'new_fml_posit': set(),
                                                               'new_fml_negat': set()})
                    
                    new_world._world_name_str = generators.new_world_name(alt_interpretation2)

                    relocate_to_new_fml_sets(new_world._formulas, fml.sub.subs[0])
                    relocate_to_new_fml_sets(new_world._formulas, fresh_atom)
                    
                    del new_world    
                    

                    #second new world
                    new_world2 = alt_interpretation2.add_world({'atoms': set(),
                                                                'neg_atoms': set(),
                                                                'double_neg': set(),
                                                                'conjunction': set(),
                                                                'neg_conjunction': interpretation.TBox_formulas,
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
                                                                'new_fml_posit': set(),
                                                                'new_fml_negat': set()})

                    new_world2._world_name_str = generators.new_world_name(alt_interpretation2)

                    relocate_to_new_fml_sets(new_world2._formulas, fml.sub.subs[0])
                    relocate_to_new_fml_sets(new_world2._formulas, forms.Negation(fresh_atom))
                    
                    del new_world2
                    
                    #we mark the orignal formula (negation of GD) as processed in the second alternative interpretation                            
                    for w_alt2 in alt_interpretation2.worlds():
                        if w_alt2._world_name_str == w._world_name_str:
                            w_alt2._formulas['neg_global_desc'].remove(fml) 
                            w_alt2._formulas['proc_negat'].update({fml}) 

                    #updating the set of formulas for which global_description_rule_3 will be blocked for this interpretation (on this branch)
                    alt_interpretation2._GlDesc_rule3_fml_set.update({fml.sub.subs[0]})                            

            
                return(interpretation, False, True, [alt_interpretation1, alt_interpretation2])

    return(interpretation, False, False, [])





# GLOBAL DESCRIPTION CUT RULE  ----------------------------



def global_description_cut_rule(interpretation):
    """ Function implementing the cut rule for global descriptions: cut(g,i) """
    
    for w in interpretation.worlds():
 
        for fml in (w._formulas['global_desc'] | w._formulas['proc_global_desc']):   
                
            for v in interpretation.worlds():
                if (fml.subs[0] not in set.union(*v._formulas.values())) and (forms.Negation(fml.subs[0]) not in set.union(*v._formulas.values())):
                    
                    alt_interpretation = deepcopy(interpretation)
                    
                    #updating current interpretation
                    relocate_to_new_fml_sets(v._formulas, fml.subs[0])

                
                    #updating the "alternative interpretation"
                    for w_alt in alt_interpretation.worlds():
                        if w_alt._world_name_str == v._world_name_str:

                            relocate_to_new_fml_sets(w_alt._formulas, forms.Negation(fml.subs[0]))

                    return(interpretation, False, True, [alt_interpretation])

    return(interpretation, False, False, [])





# LOCAL DESCRIPTION RULE 1  ----------------------------


def local_description_rule_1(interpretation):
    """ Function implementing the first rule for local descriptions: i(l,1) """

    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['local_desc'])

        for fml in fml_set_copy:        

            relocate_to_new_fml_sets(w._formulas, fml.sub)
            w._formulas['local_desc'].remove(fml) 
            w._formulas['proc_local_desc'].update({fml})  
            
            return(interpretation, False, True, [])
            
    return(interpretation, False, False, [])



# LOCAL DESCRIPTION RULE 2  ----------------------------


def local_description_rule_2(interpretation):
    """ Function implementing the second rule for local descriptions: i(l,1) """
    
    for w in interpretation.worlds():

        #here we need to iterate over all formulas, to make sure each formula in each world is checked, before "rule not applied" is returned
        for fml in (w._formulas['local_desc'] | w._formulas['proc_local_desc']):
        #in case of this rule, we consider both processed and unprocessed formulas, and do not modify any of them in course of applying the rule

            worlds_to_be_unified_names = set()
            worlds_to_be_unified_world_copies = list()

            #create working copies of the worlds to be unified            
            for v in interpretation.worlds():
                if fml.sub in set.union(*v._formulas.values()):
                    worlds_to_be_unified_names.update({v._world_name_str})
                    worlds_to_be_unified_world_copies.append(v)
            
            if len(worlds_to_be_unified_names) < 2:
                continue #to the next formula - rule not applied
            elif all([set.union(*z._formulas.values())==set.union(*worlds_to_be_unified_world_copies[0]._formulas.values()) for z in worlds_to_be_unified_world_copies[1:]]):
                continue #to the next formula - rule not applied (all the worlds have the same sets of formulas)
            else:
                formulas_sum = set.union(*[set.union(*z._formulas.values()) for z in worlds_to_be_unified_world_copies])

                for v in interpretation.worlds():
                    if v._world_name_str in worlds_to_be_unified_names:
                        for form in formulas_sum - set.union(*v._formulas.values()):
                            relocate_to_new_fml_sets(v._formulas, form)


                del worlds_to_be_unified_names
                del worlds_to_be_unified_world_copies
                
                return(interpretation, False, True, [])
                
    return(interpretation, False, False, [])
                    



# LOCAL DESCRIPTION RULE 3  ----------------------------


def local_description_rule_3(interpretation):
    """ Function implementing the rule for negated local descriptions: ~i(l) """
    
    for w in interpretation.worlds():

        fml_set_copy = list(w._formulas['neg_local_desc'])

        for fml in fml_set_copy:        
            
            if forms.Negation(fml.sub.sub) in set.union(*w._formulas.values()):
                w._formulas['neg_local_desc'].remove(fml) 
                w._formulas['proc_negat'].update({fml})
                continue 

            #creating the alternative interpetation for Option 2
            alt_interpretation = deepcopy(interpretation)

            #Option 1 - for i.C, add ~C
            #updating the current interpretation            
            relocate_to_new_fml_sets(w._formulas, forms.Negation(fml.sub.sub)) 
            w._formulas['neg_local_desc'].remove(fml) 
            w._formulas['proc_negat'].update({fml})

            #Option 2 
            if fml.sub.sub in alt_interpretation._LocDesc_rule3_list[0]:
                for w_alt in alt_interpretation.worlds():
                    if w_alt._world_name_str == w._world_name_str:
                        relocate_to_new_fml_sets(w._formulas, alt_interpretation._LocDesc_rule3_list[1][alt_interpretation._LocDesc_rule3_list[0].index(fml.sub.sub)])
                        w_alt._formulas['neg_local_desc'].remove(fml) 
                        w_alt._formulas['proc_negat'].update({fml})
                    return(interpretation, False, True, [alt_interpretation])

            else:
                fresh_atom_str = generators.new_fresh_atom(alt_interpretation)
        
                parser_tree = forms.parser_DL.parse(fresh_atom_str)
                fresh_atom = forms.ToFml().transform(parser_tree)

                for w_alt in alt_interpretation.worlds():
                    if w_alt._world_name_str == w._world_name_str:
                        relocate_to_new_fml_sets(w_alt._formulas, fresh_atom)
                        w_alt._formulas['neg_local_desc'].remove(fml) 
                        w_alt._formulas['proc_negat'].update({fml})


                #first new world
                new_world = alt_interpretation.add_world({'atoms': set(),
                                                           'neg_atoms': set(),
                                                           'double_neg': set(),
                                                           'conjunction': set(),
                                                           'neg_conjunction': interpretation.TBox_formulas,
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
                                                           'new_fml_posit': set(),
                                                           'new_fml_negat': set()})
                
                new_world._world_name_str = generators.new_world_name(alt_interpretation)

                relocate_to_new_fml_sets(new_world._formulas, fml.sub.sub)
                relocate_to_new_fml_sets(new_world._formulas, forms.Negation(fresh_atom))
                
                
                del new_world    

                #updating the special list for 
                alt_interpretation._LocDesc_rule3_list[0].append(fml.sub.sub)
                alt_interpretation._LocDesc_rule3_list[1].append(fresh_atom)

                return(interpretation, False, True, [alt_interpretation]);

    return(interpretation, False, False, [])




# LOCAL DESCRIPTION CUT RULE  ----------------------------


def local_description_cut_rule(interpretation):
    """ Function implementing the cut rule for local descriptions: cut(l,i) """
    
    for w in interpretation.worlds():
 
        for fml in (w._formulas['local_desc'] | w._formulas['proc_local_desc']):   
                
            for v in interpretation.worlds():
                if (fml.sub not in set.union(*v._formulas.values())) and (forms.Negation(fml.sub) not in set.union(*v._formulas.values())):
                    
                    alt_interpretation = deepcopy(interpretation)
                    
                    #updating current interpretation
                    relocate_to_new_fml_sets(v._formulas, fml.sub)

                    #updating the "alternative interpretation"
                    for w_alt in alt_interpretation.worlds():
                        if w_alt._world_name_str == v._world_name_str:

                            relocate_to_new_fml_sets(w_alt._formulas, forms.Negation(fml.sub))

                    return(interpretation, False, True, [alt_interpretation])


    return(interpretation, False, False, [])

