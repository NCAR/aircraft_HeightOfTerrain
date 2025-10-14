import os
import eol_scons

tools = ['default', 'prefixoptions']
env = Environment(tools=tools)

# Install HeightOfTerrain.py to $INSTALL_PREFIX/lib/HeightOfTerrain/
#env.Install('$INSTALL_PREFIX/lib/HeightOfTerrain', 'HeightOfTerrain.py')

# Optionally, if you want a symlink or copy in $INSTALL_PREFIX/bin:
env.Install('$INSTALL_PREFIX/bin', 'HeightOfTerrain')