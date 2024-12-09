#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import parse_data.prepare_data as prepare_data
import numpy as np
import matplotlib.pyplot as plt
import globals

import trajectory_analysis.trajectory_headangle as trajectory_headangle
import data_extraction.get_indices as get_indices
import analysis.loser_inferred_choice as loser_inferred_choice
import time
import analysis.wall_choice as wall_choice


# ### Functions related to the analysis of player wall choice in the context of wall visibility

# In[ ]:


# full logic for identfying first visible and chosen wall for a single player
def first_visible_wall_chosen_session(trial_list, player_id, current_fov=110, wall_sep=None, trial_type=globals.HIGH_LOW, inferred_choice=True, debug=False):
    ''' Across a whole session, return 2 binary int arrays:
        first_visible_wall_chosen - was the first visible wall on this trial (for this player) chosen?
        first_visible_wall_high - was the first visible wall on this trial (for this player) the High wall? 
        Inferred choice is used here, not just the actual outcome of the trial
        Where inferred choice is missing, or there was not exactly one wall visible at the start of a trial, 
        array elements are np.nan.
        Takes the current FoV=110, wall sep=None, trial type=globals.HIGH_LOW, and inferred choice=True. '''
    
    if debug:
        start_time = time.time()
    
    player_id = player_id
    trial_list = trial_list

    # filter trial list for HighLow trialtype
    trial_indices = get_indices.get_trials_trialtype(trial_list, trial_type=trial_type)
    trial_list = [trial_list[i] for i in trial_indices]

    if wall_sep:
        trial_indices = get_indices.get_trials_with_wall_sep(trial_list, wall_sep=wall_sep)
        trial_list = [trial_list[i] for i in trial_indices]
    
    # we want to find whether the first visible wall was chosen (or 'inferred chosen'), and whether it was the High wall
    first_visible_wall_chosen = np.ones(len(trial_list))*2
    first_visible_wall_high = np.ones(len(trial_list))*2
    
    # decide whether to include loser's inferred choice based on function inputs
    if inferred_choice:
        # get the players choice, whether this is empirical, inferred, or nan
        player_wall_choice = loser_inferred_choice.player_wall_choice_win_or_loss(trial_list, player_id)
    else:
        player_wall_choice = wall_choice.player_wall_choice_wins_only(trial_list, player_id)
    if debug:
        print(f"include loser's inferred choice status: {inferred_choice}")

    
    for i in range(len(trial_list)):

        # ----------- identify the first wall seen on this trial
        
        # get the walls for this trial
        trial = trial_list[i]
        walls = get_indices.get_walls(trial=trial)
        wall1 = walls[0]
        wall2 = walls[1]
    
        # wall_visible array for this trial 
        # boolean array of which walls are visible at each timepoint
        this_player_this_trial_wall_visible = trajectory_headangle.get_wall_visible(trial=trial, player_id=player_id, current_fov=current_fov)
        if isinstance(this_player_this_trial_wall_visible, float) and np.isnan(this_player_this_trial_wall_visible): # if trial too short to analyse
            first_visible_wall_high[i] = np.nan
            first_visible_wall_chosen[i] = np.nan
            if debug:
                print(f"Setting this trial as np.nan because of short length")
            continue
        
        # check for wall1 and wall2 being visible at the start of the trial
        (this_player_this_trial_wall1_visible,
         this_player_this_trial_wall2_visible) = trajectory_headangle.wall_visibility_player_slice_onset(this_player_this_trial_wall_visible,
                                                                                    trial)
        
        # identify which wall first becomes visible in the trial (could alternatively be neither, or both visible at the start)
        this_player_this_trial_first_visible_wall = trajectory_headangle.get_first_visible_wall(this_player_this_trial_wall_visible,
                                                                                                this_player_this_trial_wall1_visible,
                                                                                                this_player_this_trial_wall2_visible,
                                                                                                trial)
        # if debug:
            # print(f" first vis wall of trial for player: {this_player_this_trial_first_visible_wall}")
            # first_visible_wall_chosen, first_visible_wall_high = np.nan, np.nan
    
        # stop analysis if the player never sees walls or sees both at once. Set output as NaN
        if this_player_this_trial_first_visible_wall == 'neither' or this_player_this_trial_first_visible_wall == 'both':
            # set values in array to np.nan if both or neither wall are visible at the start of the trial
            # if debug:
            #     print("neither or both")
            first_visible_wall_high[i] = np.nan
            first_visible_wall_chosen[i] = np.nan
            this_player_this_trial_first_visible_wall_chosen = np.nan
    
        # condition: one wall becomes visible before the other
        else:
            # check which wall is visible initially
            if this_player_this_trial_first_visible_wall == 'wall1':
                first_visible_wall_high[i] = 1
                this_player_this_trial_first_visible_wall_num = wall1
            elif this_player_this_trial_first_visible_wall == 'wall2':
                first_visible_wall_high[i] = 0
                this_player_this_trial_first_visible_wall_num = wall2
            else:
                raise ValueError("value must be either wall1, wall2, neither, or both")
            

    # ------------

    # --------- identify player's choice on this trial

    
            # compare player choice to the first visible wall on this trial 
            # check whether player choice can be retrieved
            if np.isnan(player_wall_choice[i]):
                # set values in array to np.nan if there is no choice available
                first_visible_wall_high[i] = np.nan
                first_visible_wall_chosen[i] = np.nan
                this_player_this_trial_first_visible_wall_chosen = np.nan
                # if debug:
                #     print("not confident in loser's choice")
                #     print(f" first_vis_wall_chosen: {first_visible_wall_chosen[i]}, first_vis_wall_high: {first_visible_wall_high[i]}")
            
            else: # player choice is retrievable
                this_player_this_trial_first_visible_wall_chosen = True if player_wall_choice[i] == this_player_this_trial_first_visible_wall_num else False
                first_visible_wall_chosen[i] = this_player_this_trial_first_visible_wall_chosen

    # -------------

        # if debug:
        #     print(f" first_vis_wall_chosen: {first_visible_wall_chosen[i]}, first_vis_wall_high: {first_visible_wall_high[i]}")
        #     print(f" player_wall_choice[i]: {player_wall_choice[i]}")
        #     print(f" this_player_this_trial_first_visible_wall_chosen: {this_player_this_trial_first_visible_wall_chosen}, high wall: {wall1}")

    if debug:
        print(f"first_visible_wall_chosen_session: {first_visible_wall_chosen}")
        print(f"first_visible_wall_high_session: {first_visible_wall_high}")
    
    # output the time taken for this function
    if debug:
        end_time = time.time()
        print(f"Time taken for first_visible_wall_chosen_session (one session, one player) is {end_time-start_time:.2f}")

    return first_visible_wall_chosen, first_visible_wall_high


# In[ ]:


def get_first_visible_wall_trial(trial, player_id, current_fov, debug=False):
    ''' Returns a bool for whether the first visible wall was high, and an int for the number of the first visible wall.
        Operates on a single trial. '''
    
    # get the walls for this trial
    walls = get_indices.get_walls(trial=trial)
    wall1 = walls[0]
    wall2 = walls[1]

    if debug:
        print(f"This player, this trial high wall: {wall1}")

    # get wall_visible array for this trial to identify when a wall first becomes visible
    # boolean array of which walls are visible at each timepoint
    this_player_this_trial_wall_visible = trajectory_headangle.get_wall_visible(trial=trial, player_id=player_id, current_fov=current_fov)
    
    # return np.nan if trial is too short to analyse
    if isinstance(this_player_this_trial_wall_visible, float) and np.isnan(this_player_this_trial_wall_visible): # if trial too short to analyse
        this_player_this_trial_first_visible_wall_high = np.nan
        this_player_this_trial_first_visible_wall_num = np.nan
        if debug:
            print(f"Setting this trial as np.nan because of short length")
        return this_player_this_trial_first_visible_wall_high, this_player_this_trial_first_visible_wall_num
    
    # check for wall1 and wall2 being visible at the start of the trial
    (this_player_this_trial_wall1_visible,
    this_player_this_trial_wall2_visible) = trajectory_headangle.wall_visibility_player_slice_onset(this_player_this_trial_wall_visible,
                                                                                trial)
    
    # identify which wall first becomes visible in the trial (could alternatively be neither, or both visible at the start)
    this_player_this_trial_first_visible_wall = trajectory_headangle.get_first_visible_wall(this_player_this_trial_wall_visible,
                                                                                            this_player_this_trial_wall1_visible,
                                                                                            this_player_this_trial_wall2_visible,
                                                                                            trial)


        # first_visible_wall_chosen, first_visible_wall_high = np.nan, np.nan

    # stop analysis if the player never sees walls or sees both at once. Set output as NaN
    if this_player_this_trial_first_visible_wall == 'neither' or this_player_this_trial_first_visible_wall == 'both':
        # set values in array to np.nan if both or neither wall are visible at the start of the trial
        if debug:
            print("neither or both")
        this_player_this_trial_first_visible_wall_high = np.nan
        this_player_this_trial_first_visible_wall_num = np.nan

    # condition: one wall becomes visible before the other
    else:
        # check which wall is visible initially
        if this_player_this_trial_first_visible_wall == 'wall1':
            this_player_this_trial_first_visible_wall_high = 1
            this_player_this_trial_first_visible_wall_num = wall1
        elif this_player_this_trial_first_visible_wall == 'wall2':
            this_player_this_trial_first_visible_wall_high = 0
            this_player_this_trial_first_visible_wall_num = wall2
        else:
            raise ValueError("value must be either wall1, wall2, neither, or both")
        
    if debug:
        print(f" first vis wall of trial for player: {this_player_this_trial_first_visible_wall}")
        print(f" first_vis_wall_chosen: {this_player_this_trial_first_visible_wall_num}, first_vis_wall_high: {this_player_this_trial_first_visible_wall_high}")
        
    return this_player_this_trial_first_visible_wall_high, this_player_this_trial_first_visible_wall_num


# In[ ]:


def get_player_choice_trial(player_wall_choice, trial_idx, this_player_this_trial_first_visible_wall_num, debug=False):
    ''' Returns a bool for whether the first visible wall was chosen on this trial '''

    
    # immediately return np.nan if there was not a first visible wall for this player, trial
    if np.isnan(this_player_this_trial_first_visible_wall_num):
        return np.nan
    
    # get the wall choice of this player for this trial (inferred or not will depend on how the parent function was called)
    this_trial_player_wall_choice = player_wall_choice[trial_idx]
    
    if debug:
        print(f" player wall choice this trial: {this_trial_player_wall_choice}")

    # compare player choice to the first visible wall on this trial 
    # check whether player choice can be retrieved
    if np.isnan(this_trial_player_wall_choice):
        # set values in array to np.nan if there is no choice available
        first_visible_wall_chosen = np.nan
        if debug:
            print("not confident in loser's choice, or inferred choice not used")
            print(f" first_vis_wall_chosen: {first_visible_wall_chosen}")
    
    else: # player choice is retrievable
        # does the first visible wall for this player match their choice? 
        first_visible_wall_chosen = True if this_trial_player_wall_choice == this_player_this_trial_first_visible_wall_num else False

    if debug:
        print(f" this_player_this_trial_first_visible_wall_chosen: {first_visible_wall_chosen}")

    return first_visible_wall_chosen


# In[ ]:


# full logic for identfying first visible and chosen wall for a single player
def first_visible_wall_chosen_session_remake(trial_list, player_id, current_fov=110, wall_sep=None, trial_type=globals.HIGH_LOW, inferred_choice=True, debug=False):
    ''' Across a whole session, return 2 binary int arrays:
        first_visible_wall_chosen - was the first visible wall on this trial (for this player) chosen?
        first_visible_wall_high - was the first visible wall on this trial (for this player) the High wall? 
        Inferred choice is used here, not just the actual outcome of the trial
        Where inferred choice is missing, or there was not exactly one wall visible at the start of a trial, 
        array elements are np.nan.
        Takes the current FoV=110, wall sep=None, trial type=globals.HIGH_LOW, and inferred choice=True. '''
    
    # timing this function
    if debug:
        start_time = time.time()
    
    # filter trial list for HighLow trialtype
    trial_indices = get_indices.get_trials_trialtype(trial_list, trial_type=trial_type)
    trial_list = [trial_list[i] for i in trial_indices]

    # filter trial list for wall separations if specified
    if wall_sep:
        trial_indices = get_indices.get_trials_with_wall_sep(trial_list, wall_sep=wall_sep)
        trial_list = [trial_list[i] for i in trial_indices]
    
    # we want to find whether the first visible wall was chosen (or 'inferred chosen'), and whether it was the High wall
    first_visible_wall_chosen_session = np.ones(len(trial_list))*2
    first_visible_wall_high_session = np.ones(len(trial_list))*2
    
    # decide whether to include loser's inferred choice based on function inputs
    if inferred_choice:
        # get the players choice, whether this is empirical, inferred, or nan
        player_wall_choice = loser_inferred_choice.player_wall_choice_win_or_loss(trial_list, player_id, debug=debug)
    else:
        player_wall_choice = wall_choice.player_wall_choice_wins_only(trial_list, player_id, debug=debug)
    if debug:
        print(f"include loser's inferred choice status: {inferred_choice}")
        print(f"player wall choices for this player: {player_wall_choice}")
    
    # for each trial, get the first visible wall number, whether it was high, and whether it was chosen
    for trial_idx, trial in enumerate(trial_list):
        
        # use wall visibility through the trial to identify which walls of the walls are seen first
        this_trial_first_visible_wall_high, this_player_this_trial_first_visible_wall_num = get_first_visible_wall_trial(trial, player_id, current_fov)

        # check against player choices to see if the first visible wall was chosen
        this_trial_first_visible_wall_chosen = get_player_choice_trial(player_wall_choice, trial_idx, this_player_this_trial_first_visible_wall_num)

        # set everything equal to nan if we cannot retrieve player choice (we don't want to include trials in analysis
        # unless they contain all information)
        if np.isnan(this_trial_first_visible_wall_chosen):
            this_trial_first_visible_wall_high = np.nan
            this_player_this_trial_first_visible_wall_num = np.nan

        # add results to array for the full session for this player
        first_visible_wall_chosen_session[trial_idx] = this_trial_first_visible_wall_chosen
        first_visible_wall_high_session[trial_idx] = this_trial_first_visible_wall_high

    if debug:
        print(f"For player {player_id}")
        print(f"first_visible_wall_chosen_session: {first_visible_wall_chosen_session}")
        print(f"first_visible_wall_high_session: {first_visible_wall_high_session}")


    # output the time taken for this function
    if debug:
        end_time = time.time()
        print(f"Time taken for first_visible_wall_chosen_session (one session, one player) is {end_time-start_time:.2f}")

    return first_visible_wall_chosen_session, first_visible_wall_high_session


# In[ ]:


def probability_first_visible_wall_chosen_and_low(first_visible_wall_chosen, first_visible_wall_high, reverse=False, debug=False):
    ''' Returns a probability value for the first wall being chosen when the first wall is low.
        Takes two binary int arrays of len(trials_list), for the first visible wall being chosen, and for
        the first visible wall being high.
        If there is no choice or loser's inferred choice, input array values are np.nan.
        If both walls were initially visible, or never become visible, input array values are np.nan.
        Assumes data from a single player's session.'''


    if debug:
        print(f"Number of trials total is: {first_visible_wall_chosen.size}")
    
    # if we are reversed (analyse High, not Low), change the array into a boolean of the first visible wall being high
    # instead of low
    if reverse:
        first_visible_wall_condition = first_visible_wall_high
    else:
        first_visible_wall_condition = (first_visible_wall_high -1) * -1

    # restrict data to the first visible wall being the condition, and also being chosen
    # both of these array will have nan values where there is no confident loser's choice data, or where there was not a first visible wall
    first_visible_condition_and_also_chosen= np.where(
                    np.isnan(first_visible_wall_chosen) | np.isnan(first_visible_wall_condition),   # If either element is nan
                    np.nan,                                           # Set to np.nan
                    np.where((first_visible_wall_chosen == 1.) & (first_visible_wall_condition == 1), 1., 0.)  # Else set to 1. or 0.
     )



    # remove nans from the analysis
    first_visible_wall_condition_not_nan = first_visible_wall_condition[~np.isnan(first_visible_wall_condition)]
    first_visible_wall_condition_and_also_chosen_not_nan = first_visible_condition_and_also_chosen[~np.isnan(first_visible_condition_and_also_chosen)]

        
    if debug:
        print(f"Number of trials for this player that begin with one wall visible and a retrievable choice is: " +
                f"{first_visible_wall_condition_and_also_chosen_not_nan.size}")
        print(f"size first_visible_condition_and_also_chosen: {first_visible_condition_and_also_chosen.size}"
              + f" size first_visible_wall_condition_and_also_chosen_not_nan: {first_visible_wall_condition_and_also_chosen_not_nan.size}")
    
    first_visible_wall_high_not_nan = first_visible_wall_high[~np.isnan(first_visible_wall_high)]
    
    if debug:
        print(f"Number of trials for this player that begin with Condition wall visible and end with a retrievable choice is: " +
                f"{first_visible_wall_condition_not_nan[first_visible_wall_condition_not_nan ==1].size}")
        print(f"Number of trials for this player that begin with Condition wall visible and end with Condition wall chosen is: " +
                f"{first_visible_wall_condition_and_also_chosen_not_nan[first_visible_wall_condition_and_also_chosen_not_nan ==1].size}")
        print(f"Number of trials for this player that begin with High wall visible and end with a retrievable choice is: " +
                f"{first_visible_wall_high_not_nan[first_visible_wall_high_not_nan ==1].size}")
        
    # probability of first wall being chosen when the first wall is low
    num_trials_first_visible_condition_and_also_chosen_not_nan = first_visible_wall_condition_and_also_chosen_not_nan[first_visible_wall_condition_and_also_chosen_not_nan ==1].size
    num_trials_first_visible_condition_not_nan = first_visible_wall_condition_not_nan[first_visible_wall_condition_not_nan ==1].size
    try:
        probability_first_wall_chosen_when_condition = num_trials_first_visible_condition_and_also_chosen_not_nan/num_trials_first_visible_condition_not_nan
    except ZeroDivisionError:
        print(f"num_trials_first_visible_condition_and_also_chosen_not_nan size: {num_trials_first_visible_condition_and_also_chosen_not_nan}," +
              f"num_trials_first_visible_condition_not_nan: {num_trials_first_visible_condition_not_nan}")
        probability_first_wall_chosen_when_condition = np.nan
    
    if debug:
        print(f"num_walls_first_visible_condition_and_also_chosen_not_nan = {num_trials_first_visible_condition_and_also_chosen_not_nan}")
        print(f"num_walls_first_visible_condition_not_nan = {num_trials_first_visible_condition_not_nan}")
        print(f"Probability of first wall being chosen when the first wall is condition: " + f"{probability_first_wall_chosen_when_condition}")
        print(f"trials where condition was seen first and was chosen: {num_trials_first_visible_condition_and_also_chosen_not_nan}")
    
    return probability_first_wall_chosen_when_condition, num_trials_first_visible_condition_and_also_chosen_not_nan


# In[ ]:


def probability_first_wall_chosen_and_low_multiple_sessions_df(trial_lists, wall_sep=None, trial_type=globals.HIGH_LOW, reverse=False, inferred_choice=False, debug=False):
    ''' Returns an array of probabilities for the first wall being chosen when the first wall is low
        and an array of the number of times this ocurred.
        These are of shape num_sessions*num_players.
        Inferred choice is used here (first_visible_wall_chosen_session).
        Takes a data folder path string, and a list of all json filenames (one for each session of data) '''
    
    num_sessions = len(trial_lists)
    probability_first_wall_chosen_array = np.zeros((num_sessions,2))
    probability_first_wall_chosen_when_condition_array = np.zeros((num_sessions,2))
    times_first_wall_chosen_when_condition_array = np.zeros((num_sessions,2))

    # for each session data file, identify probability of choosing first wall seen when that wall is Low
    for trial_list_idx in range(len(trial_lists)):
        print(f"trial list index: {trial_list_idx}")
        this_trial_list = trial_lists[trial_list_idx]
        for player_id in range(2): # for each player
            print(f"player num: {player_id}")
            first_visible_wall_chosen, first_visible_wall_high = first_visible_wall_chosen_session_remake(this_trial_list, player_id=player_id, wall_sep=wall_sep, trial_type=trial_type, inferred_choice=inferred_choice, debug=debug)

            # quick detour to get the probability of choosing the first visible wall
            first_visible_wall_chosen_not_nan = first_visible_wall_chosen[~np.isnan(first_visible_wall_chosen)] # remove nan values
            num_first_visible_wall_chosen = first_visible_wall_chosen_not_nan[first_visible_wall_chosen_not_nan == 1].size # count the ones in nan-removed array
            probability_first_wall_chosen_array[trial_list_idx, player_id] = num_first_visible_wall_chosen/first_visible_wall_chosen_not_nan.size # count of 1s against count of 1s and 0s (nans removed)

            # calculate probability choosing condition        
            probability_first_wall_chosen_when_condition, times_first_wall_chosen_when_condition = probability_first_visible_wall_chosen_and_low(first_visible_wall_chosen, first_visible_wall_high, reverse=reverse)
            probability_first_wall_chosen_when_condition_array[trial_list_idx, player_id] = probability_first_wall_chosen_when_condition
            times_first_wall_chosen_when_condition_array[trial_list_idx, player_id] = times_first_wall_chosen_when_condition 

    return probability_first_wall_chosen_when_condition_array, times_first_wall_chosen_when_condition_array, probability_first_wall_chosen_array

