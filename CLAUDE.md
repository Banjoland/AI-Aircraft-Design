## AI Aircraft Design

Your purpose is to design an aircraft to perform as closely as possible to the specifications detailed in the file SPECIFICATION.md.  

## Design and simulation software

You will use the OpenVSP aircraft design and analysis softare suite.  The software is located in the directory: C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64

There is documentation in that folder, including a Python API documentation as well as a custom scripting language used by the program. 

Additional documentation can be found at the website: https://openvsp.org/

There were two previous attempts at this project.  You can review those directories to aid in design and tooling.  Those directories are:

- "C:\Users\asgin\OneDrive\Documents\PROJECTS\AI AIRPLANE DESIGN\AIRPLANE DESIGN CLAUDE"
- "C:\Users\asgin\OneDrive\Documents\PROJECTS\AI AIRPLANE DESIGN\AIRPLANE DESIGN CODEX"

## Project initialization

Read all of the markdown files in this project and format accordingly

##  Project structure and guidelines

- At every step of the project, you should record what you do in LOG.md.  The purpose is to provide a succinct summary of the decisions you made and whether or not those decisions resulted in a design that better performed to the specification than the last
- Aircraft designs should be located in the AIRCRAFT directory.  For each design, create a new model file with the filename MODEL_MM_DD_HH_MM_SS.vsp3
- At each step of the process you will determine if you have the tools and/or skills necessary to perform the task.  If you do not, you should create the tools or skills necessary to complete the task.
- For each significant task, subagents should be used to focus on that task and load only the context required to complete the task.
- Each agent should have access to their own set of tools and skills.  In addition to generating the tool or skill, you should create a README.md that instructs human readers what the agent does.  For each agent there should be a subdirectory made called TEST that contains models, documents etc that can allow a human user to verify the tools you make on prototype/test aircraft models

## Your Process

The design process will be iterative.  Each time you are called, you will change only one aspect of the aircraft.  Each iteration you will do the following operations:

1. Perform a simulation on the aircraft.   Simulations should be performed in the SIMULATION directory.  Read your instructions in that directory for further information.  In the SIMULATION directory there is a file called SIM_SPEC.md.  It lists requried analysis for each Aircraft.  

2.  Evaluate performance.  Based on the results of the simulation you will score each aircraft.  Evaluations are performed in the directory called EVALUATION.  Read your instructions in that directory for further information.  Aircraft are scored using cost functions. Cost functions are defined in EVALUATION/COST FUNCTION.md.  The purpose of cost functions is to rank performance features based on relative importance.  You will write a short, formatted report in the log file that discusses your findnings.

3.  Iterate the design.  Based on the evaluation of the aircraft model, and the knowledge you've stored in the log file, you will determine one feature of the aircraft to change.  You will make a copy of the current model and make that the new model.  You will change the one feature that you determine will MOST improve the evaluation score.

4.  Repeat this process, starting on step 1 above.  Even if you've met the specification, you will continue to iterate to improve the evaluation score.  Lighter, faster, with a more efficent airfoil and elegant curves.

## Unit

Units for this project shall always be SI Units

If I specify imperial units in any document, you will compute new values in SI units and over write the imperial units

## Structure and Philosophy

The primary purpose of this project is to develope the tools and skills necessary to creatively design and analyze airplanes.  Your aircraft design is important, not for the design itself, but to validate your ability to design and analyze the airplane. To validated your tools and skills

## skills

When the word "Skills" is used in this project, I mean formal agent skills as defined by https://agentskills.io/home

## tools

When the word "tools" is used in this project, I mean python programs and (optionally) sub-agents that can run those programs.