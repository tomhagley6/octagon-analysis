#!/usr/bin/env python
# coding: utf-8

# In[1]:


import parse_data.prepare_data as prepare_data
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import globals
import plotting.plot_trajectory as plot_trajectory
import plotting.plot_octagon as plot_octagon
import data_extraction.extract_trial as extract_trial
import math
import trajectory_analysis.trajectory_vectors as trajectory_vectors
import trajectory_analysis.trajectory_direction as trajectory_direction
import data_extraction.get_indices as get_indices


# In[ ]:


def extract_final_third_trajectory(trajectory):
    ''' Takes 2*timepoints trajectory array of vstacked x_coords, y_coords
        Returns final third of input array '''
    
    trajectory_length = trajectory.shape[1]
    truncated_length = int(np.floor(trajectory_length*(2/3)).item())

    final_third_trajectory = trajectory[:,truncated_length:trajectory_length]

    return final_third_trajectory
    
    


# In[ ]:


def average_most_aligned_wall_trajectory(cosine_similarity_trajectory):
    ''' Takes num_walls*timepoints cosine similarity array (to wall centres)
        Return index of the most aligned (on average) wall to the trajectory '''
     
    return np.argmax(np.nanmean(cosine_similarity_trajectory, axis=1))
    
    


# In[ ]:


def proportion_trajectory_aligned_with_average(cosine_similarity_trajectory, most_aligned_wall):
    ''' Takes num_walls*timepoints array and scalar
        Return the proportion of timepoints in which the most aligned wall is the same as the average
        Currently unused '''
    
    count_aligned = 0
    for i in range(cosine_similarity_trajectory.shape[1]):
        cosine_similarity_this_timepoint = cosine_similarity_trajectory[:,i]
        most_aligned_wall_this_timepoint = np.argmax(cosine_similarity_this_timepoint)
        if most_aligned_wall_this_timepoint == most_aligned_wall:
            count_aligned += 1

    try:
        proportion_timepoints_aligned = count_aligned/cosine_similarity_trajectory.shape[1]
    except ZeroDivisionError:
        print("cosine_similarity_trajectory.shape[1] == 0")
        proportion_timepoints_aligned = 0
        
    return proportion_timepoints_aligned
        


# In[ ]:


def difference_to_second_highest_alignment(cosine_similarity_trajectory):
    ''' Takes num_walls*timepoints cosine similarity array (to wall centres)
        Returns the difference between the average most aligned wall and average
        second most aligned wall ''' 

    # average cosine similarities across timepoints
    average_cosine_similarities = np.nanmean(cosine_similarity_trajectory, axis=1)

    # find the most aligned wall and the alignment value
    most_aligned_wall_alignment = np.max(average_cosine_similarities)

    # repeat for the second highest alignment
    average_cosine_similarities_remove_max = average_cosine_similarities[average_cosine_similarities != most_aligned_wall_alignment]
    second_most_aligned_wall_alignment = np.max(average_cosine_similarities_remove_max)

    # return the difference
    return most_aligned_wall_alignment - second_most_aligned_wall_alignment



# In[ ]:


def final_distance_to_wall(trajectory, average_most_aligned_wall_index):
    ''' Takes a 2*timepoints trajectory array and the average most aligned wall index
        throughout a relevant portion of the trajectory
        Returns the final distance between the player location and the most aligned wall '''

    alcove_centre_points = plot_octagon.return_alcove_centre_points()

    final_position = trajectory[:,-1]
    most_aligned_wall_location = alcove_centre_points[:,average_most_aligned_wall_index]

    return np.linalg.norm(most_aligned_wall_location - final_position)


# In[ ]:


# umbrella function to extract loser's choice for one trial
def infer_loser_choice_trial(trial_list, trial_index, loser_ids, window_size=5):
    ''' Given a trial list and index, and 1D array of loser id ints, find the most
        aligned wall for the loser in the latter part of their trajectory, and decide
        whether this most aligned wall should be considered their choice
        For a single trial
        Returns: scalar wall most aligned with on average, boolean confidence of loser's choice '''
    
    # LVs 
    losers_choice_accepted = False
    
    # get trial and loser id
    trial = trial_list[trial_index]
    loser_id = loser_ids[trial_index]

    # get trajectory for loser
    trajectory = trajectory_vectors.extract_trial_player_trajectory(trial=trial, player_id=loser_id)
    
    # ignore first half of trajectory
    trajectory_end = extract_final_third_trajectory(trajectory)
    
    # fine cosine similarities between trajectory direction vector and player-alcove vectors for each wall
    cosine_similarity_trajectory = trajectory_direction.cosine_similarity_throughout_trajectory(trajectory_end,
                                                                                            window_size=window_size,
                                                                                            num_walls=8,
                                                                                            calculate_thetas=False)
    # find the most aligned wall (mean average)
    average_most_aligned_wall_index = average_most_aligned_wall_trajectory(cosine_similarity_trajectory)
    average_most_aligned_wall_num = average_most_aligned_wall_index + 1
    highest_alignment_val = np.max(np.nanmean(cosine_similarity_trajectory, axis=1))

    # find the distance to the most aligned wall at the final trajectory timepoint
    final_distance_most_aligned_wall = final_distance_to_wall(trajectory, average_most_aligned_wall_index)


    # # confidence checks
    # # find the fraction of timepoints in which the most aligned wall was the same as the average for the trajectory
    # proportion_timepoints_aligned = proportion_trajectory_aligned_with_average(cosine_similarity_trajectory, average_most_aligned_wall_index)
    # # difference in average cosine similarity between the most and next most aligned wall
    # difference_to_second_highest_alignment_val = difference_to_second_highest_alignment(cosine_similarity_trajectory)

    # # decide whether to accept the loser's choice
    # if proportion_timepoints_aligned > 0.60 and difference_to_second_highest_alignment_val > 0.08:
    #     losers_choice_accepted = True

    # decide whether to accept the loser's choice
    if highest_alignment_val > 0.875:
        losers_choice_accepted = True
    elif final_distance_most_aligned_wall < 4:
        losers_choice_accepted = True

    return average_most_aligned_wall_num, losers_choice_accepted

    
    


# In[ ]:


# umbrella function to extract loser's choice for all trials in a list
def infer_loser_choice_session(trial_list):
    ''' Given a trial list find the most aligned wall for the loser 
        in the second half of their trajectory, and decide
        whether this most aligned wall should be considered their choice,
        for all trials 
        Return an array of most aligned walls and a boolean array of confidence
        (Both 1D of size len(trial_list)) '''

    # initialise
    loser_inferred_choice = np.zeros(len(trial_list))
    loser_inferred_choice_confidence = np.zeros(len(trial_list), dtype=np.bool)
    
    # find the loser IDs for each trial 
    winner_ids = get_indices.get_trigger_activators(trial_list)
    loser_ids = (winner_ids -1) * -1

    # get choice and confidence for each trial
    for trial_index in range(len(trial_list)):
        this_loser_inferred_choice, this_loser_inferred_choice_confidence = infer_loser_choice_trial(trial_list, trial_index, loser_ids)
        loser_inferred_choice[trial_index] = this_loser_inferred_choice
        loser_inferred_choice_confidence[trial_index] = this_loser_inferred_choice_confidence


    return loser_inferred_choice, loser_inferred_choice_confidence


# In[ ]:


## COMBINED WITH ACTUAL CHOICES ## 


# In[ ]:


def player_wall_choice_win_or_loss(trials_list, player_id):
    ''' Logic for identifying the player's chosen wall whether they lost the trial or not
        Returns int array of size len(trials_list) of chosen wall numbers (or np.nan) '''
    
    winning_player = get_indices.get_trigger_activators(trials_list)
    chosen_walls = get_indices.get_chosen_walls(trials_list)
    loser_inferred_choices, loser_inferred_choice_confidences = infer_loser_choice_session(trials_list)
    current_player_wall_choice = np.zeros(len(trials_list))
    
    for trial_index in range(len(trials_list)):
        if player_id != winning_player[trial_index]:
            if loser_inferred_choice_confidences[trial_index] == False:
                wall_chosen = np.nan
            elif loser_inferred_choice_confidences[trial_index] == True:
                wall_chosen = loser_inferred_choices[trial_index] 
            else:
                raise ValueError("Boolean array must be given for loser_inferred_choice_confidences")
        elif player_id == winning_player[trial_index]:
            wall_chosen = chosen_walls[trial_index]
    
        current_player_wall_choice[trial_index] = wall_chosen

    return current_player_wall_choice

