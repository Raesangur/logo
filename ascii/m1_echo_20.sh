#!/bin/bash

bold=$(tput bold)
normal=$(tput sgr0)
red='\033[0;31m'
nc='\033[0m' # No Color

echo -e "${bold}@@@@@@@      ${red}&&&&&&&${nc}"
echo -e "@@@@@@@@@  ${red}&&&&&&&&&${nc}"
echo -e "@@@@@@@@@@${red}&&&&&&&&&&${nc}"
echo -e "@@@@@@@@@@@@@@@${red}&&&&&${nc}"
echo -e "@@@@@ @@@@@@@@ ${red}&&&&&${nc}"
echo -e "@@@@@   @@@@   ${red}&&&&&${nc}"
echo -e "@@@@@          ${red}&&&&&${nc}"
echo -e "@@@@@          ${red}&&&&&${nc}"
echo -e "@@@@@          ${red}&&&&&${nc}"
echo -e "@@@@@          ${red}&&&&&${nc}"
echo -e "@@@@@          ${red}&&&&&${nc}${normal}"

