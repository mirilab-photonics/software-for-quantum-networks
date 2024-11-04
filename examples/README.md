# Examples #

This directory contains examples demonstrating both the implementation of individual components and their integration into broader simulations. The following modules are implemented:

- **[coherent_source.py](./coherent_source.py)**: Generates a coherent state within a provided space, starting from the vacuum state, and accounts for errors due to truncation.
- **[fiber.py](./fiber.py)**: Defines operators that introduce phase shifts and attenuation effects on the given state.
- **[memory.py](./memory.py)**: Simulates the storage of a single photon.
- **[memory_error.py](./memory_error.py)**: Simulates the storage of a single photon, but introduces errors due to simplifications.
- **[single_photon_source.py](./single_photon_source.py)**: Generates a single photon state from an initial vacuum state.
- **[color_center.py](./color_center.py)**: Rudimentary example on the implementation of the color center. It does not work in that it doesn't correctly simulate nv centers, but it does provide the necesarry toolset to implement a correct simulation. Example of usage is included in the [example_4.ipynb](./example_4.ipynb).
These modules are utilized in various example files to illustrate their functionality and application in different scenarios.
