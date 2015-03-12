#Name: ebtel2fl_configure_runs
#Author: Will Barnes
#Date: 17 February 2014

#Description: Configure EBTEL-2fluid runs

#Set up root directory extension
root = '/data/datadrive2/EBTEL-2fluid_runs/'
root_ebtel2fl = '/home/wtb2/Documents/EBTEL-2fluid_repo/'

#Import necessary modules
import sys
sys.path.append(root_ebtel2fl + 'bin/')
import ebtel2fl_wrapper as ew
import numpy as np
import argparse

#Declare parser object
parser = argparse.ArgumentParser(description='Script that prints configuration files for EBTEL-2fluid runs.')

#Add arguments to parser
parser.add_argument("-s","--species",help="Species to which the heating was applied for particular run.")
parser.add_argument("-as","--amp_switch",help="Switch to decide between power-law and uniform heating.")
parser.add_argument("-a","--alpha",type=float,help="Spectral index for the power-law distribution used.")
parser.add_argument("-L","--loop_length",type=float,help="Loop half-length.")
parser.add_argument("-t","--t_pulse",type=float,help="Width of the heating pulse used for the particular run.")
parser.add_argument("-S","--solver",help="Solver used to compute solutions.")

#Declare the parser dictionary
args = parser.parse_args()

#Define function that chooses amplitude from power-law distribution for given index alpha
def power_law_dist(x0, x1, x, alpha):
    return ((x1**(alpha+1) - x0**(alpha+1))*x + x0**(alpha+1))**(1/(alpha+1))

#Define the function that configures the start, end time arrays
def config_amp_start_end_time(t_wait, t_total, t_pulse, amp0, amp1, alpha):
    #Calculate the number of pulses
    N = int(np.ceil(t_total/(t_pulse + t_wait)))

    #Create the needed arrays
    t_start_array = np.empty([N])
    t_end_array = np.empty([N])
    amp_array = np.empty([N])

    #Loop over number of events
    for i in range(N):
        #Create start and end time arrays
        t_start_array[i] = i*(t_pulse + t_wait)
        t_end_array[i] = t_start_array[i] + t_pulse
        #Generate random number for pl distribution
        x = np.random.rand(1)
        #Generate amplitude array
        amp_array[i] = power_law_dist(amp0,amp1,x,alpha)

    return {'num_events':N,'t_start_array':t_start_array,'t_end_array':t_end_array,'amp_array':amp_array}


#Set heating parameters
Q0 = 1e+23 #lower bound on nanoflare energy
Q1 = 1e+25 #upper bound on nanoflare energy
Ah = 1e+14 #loop cross sectional area
Hn = 8.3e-3 #Average nanoflare energy distributed over the total time

#Set up array of wait times
T_wait = np.arange(250,5250,250)
#Set the pulse duration
t_pulse = args.t_pulse

#Configure static parameters
config_dict = {'usage_option':'dem','rad_option':'rk','dem_option':'new','heat_flux_option':'limited','solver':args.solver,'ic_mode':'st_eq'}
config_dict['total_time'] = 80000
config_dict['tau'] = 1.0
config_dict['rka_error'] = 1.0e-6
config_dict['index_dem'] = 451
config_dict['sat_limit'] = 0.166667
config_dict['h_back'] = 3.4e-6
config_dict['heating_shape'] = 'triangle'
config_dict['t_start_switch'] = 'file'
config_dict['t_end_switch'] = 'file'
config_dict['T0'] = 1.0e+6
config_dict['n0'] = 1.0e+8
config_dict['t_start'] = 0.0
config_dict['t_pulse_half'] = 50.0
config_dict['mean_t_start'] = 1000
config_dict['std_t_start'] = 1000

#Configure directory-level parameters
config_dict['heat_species'] = args.species
config_dict['amp_switch'] = args.amp_switch
config_dict['alpha'] = args.alpha
config_dict['loop_length'] = args.loop_length
config_dict['amp0'] = Q0/(config_dict['loop_length']*1.0e+8*Ah*t_pulse) #lower bound on nanoflare volumetric heating rate
config_dict['amp1'] = Q1/(config_dict['loop_length']*1.0e+8*Ah*t_pulse) #upper bound on nanoflare volumetric heating rate

#Set up directory to print config files
top_dir = config_dict['heat_species']+'_heating_runs/'
if config_dict['amp_switch'] == 'uniform':
    top_dir = top_dir + 'alpha' + config_dict['amp_switch'] + '/'
else:
    top_dir = top_dir + 'alpha' + str(-1*config_dict['alpha']) + '/'
config_dir = root + top_dir + 'config/'
data_dir = root + top_dir + 'data/'

#Loop over different values of time between successive nanoflares
for i in range(len(T_wait)):

    #Calculate the start and end time arrays and the number of events
    heat_times = config_amp_start_end_time(T_wait[i], config_dict['total_time'], t_pulse,config_dict['amp0'], config_dict['amp1'], config_dict['alpha'])
    config_dict['num_events'] = heat_times['num_events']
    config_dict['start_time_array'] = heat_times['t_start_array']
    config_dict['end_time_array'] = heat_times['t_end_array']
    if config_dict['amp_switch'] == 'file':
        #Set the amplitude array
        config_dict['amp_array'] = heat_times['amp_array']
  
    #Set the uniform peak nanoflare energy (for triangular pulses)
    config_dict['h_nano'] = 2*Hn*config_dict['total_time']/(config_dict['num_events']*t_pulse)

    #Concatenate the filename
    fn = 'ebtel2fl_L' + str(config_dict['loop_length']) + '_tn' + str(T_wait[i]) + '_tpulse' + str(t_pulse) + '_' + config_dict['solver']

    #Set the ouput filename
    config_dict['output_file'] = data_dir + fn

    #Print the config file (use same filename as output with _config)
    ew.print_xml_config(config_dict,config_file=config_dir+fn+'.xml')
