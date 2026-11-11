#!/bin/bash
# Mac: quita el arranque automático de Alfred.
PLIST="$HOME/Library/LaunchAgents/cl.alfred.servicio.plist"
launchctl unload "$PLIST" 2>/dev/null; rm -f "$PLIST"
echo "Alfred ya no arranca solo. (En Windows: borra Alfred.vbs de shell:startup)"
