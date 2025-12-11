#!/bin/bash
# Quick launch script for ROS game nodes
# This script launches all required ROS nodes for the Rat Race game

set -e  # Exit on error

echo "=========================================="
echo "  Rat Race - ROS Game Launcher"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}INFO:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Check if ROS is installed
if ! command -v roscore &> /dev/null; then
    print_error "ROS is not installed or not in PATH"
    echo ""
    echo "Please install ROS and source the setup.bash file:"
    echo "  source /opt/ros/noetic/setup.bash  # For ROS Noetic"
    echo "  # OR"
    echo "  source /opt/ros/melodic/setup.bash  # For ROS Melodic"
    exit 1
fi
print_success "ROS is installed"

# Check if roscore is running
if ! rostopic list &> /dev/null; then
    print_error "ROS Master (roscore) is not running!"
    echo ""
    echo "Please start roscore in a separate terminal first:"
    echo "  roscore"
    echo ""
    echo "Then run this script again."
    exit 1
fi
print_success "ROS Master (roscore) is running"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
print_info "Working directory: $SCRIPT_DIR"

# Source ROS base setup
if [ -f /opt/ros/noetic/setup.bash ]; then
    source /opt/ros/noetic/setup.bash
    print_success "Sourced ROS Noetic"
elif [ -f /opt/ros/melodic/setup.bash ]; then
    source /opt/ros/melodic/setup.bash
    print_success "Sourced ROS Melodic"
else
    print_warning "Could not find ROS setup.bash, assuming ROS is already sourced"
fi

# Check if using catkin workspace
if [ -f ~/catkin_ws/devel/setup.bash ]; then
    source ~/catkin_ws/devel/setup.bash
    print_success "Sourced catkin workspace"
    
    # Check if ros_nodes is in catkin workspace
    if [ -d ~/catkin_ws/src/ros_nodes ]; then
        print_success "Found ros_nodes in catkin workspace"
    else
        print_warning "ros_nodes not in catkin workspace, will add to ROS_PACKAGE_PATH"
    fi
fi

# Always add project directory to ROS_PACKAGE_PATH (after sourcing to ensure it's not overwritten)
# This ensures ros_nodes can be found even if not in catkin workspace
export ROS_PACKAGE_PATH=$(pwd):$ROS_PACKAGE_PATH
print_info "Added $(pwd) to ROS_PACKAGE_PATH (prepended for priority)"

# Verify ros_nodes package can be found
print_info "Verifying ros_nodes package can be found..."
if rospack find ros_nodes &> /dev/null; then
    ROS_NODES_PATH=$(rospack find ros_nodes)
    print_success "ros_nodes package found: $ROS_NODES_PATH"
else
    print_error "ros_nodes package not found in ROS_PACKAGE_PATH"
    echo ""
    echo "Current ROS_PACKAGE_PATH: $ROS_PACKAGE_PATH"
    echo "Current directory: $(pwd)"
    echo "ros_nodes directory exists: $([ -d ros_nodes ] && echo 'YES' || echo 'NO')"
    echo ""
    echo "Trying alternative approach..."
    
    # Try using absolute path
    ABS_PATH=$(cd "$(pwd)" && pwd)
    export ROS_PACKAGE_PATH=$ABS_PATH:$ROS_PACKAGE_PATH
    print_info "Updated ROS_PACKAGE_PATH with absolute path: $ABS_PATH"
    
    # Try again
    if rospack find ros_nodes &> /dev/null; then
        ROS_NODES_PATH=$(rospack find ros_nodes)
        print_success "ros_nodes package now found: $ROS_NODES_PATH"
    else
        print_error "Still cannot find ros_nodes package"
        echo ""
        echo "Troubleshooting steps:"
        echo "  1. Verify you're in the correct directory:"
        echo "     cd ~/RP_Moreno_Turkel_25"
        echo "  2. Check ros_nodes exists:"
        echo "     ls -la ros_nodes/"
        echo "  3. Try manually setting ROS_PACKAGE_PATH:"
        echo "     export ROS_PACKAGE_PATH=\$HOME/RP_Moreno_Turkel_25:\$ROS_PACKAGE_PATH"
        echo "     rospack find ros_nodes"
        echo "  4. Or build in catkin workspace:"
        echo "     cd ~/catkin_ws/src"
        echo "     ln -s ~/RP_Moreno_Turkel_25/ros_nodes ros_nodes"
        echo "     cd ~/catkin_ws && catkin_make"
        exit 1
    fi
fi

# Make sure nodes are executable
if [ -d "ros_nodes" ]; then
    chmod +x ros_nodes/*.py 2>/dev/null || true
    print_success "Made all Python nodes executable"
else
    print_error "ros_nodes directory not found!"
    exit 1
fi

# Check if launch file exists
if [ ! -f "ros_nodes/launch/game.launch" ]; then
    print_error "Launch file not found: ros_nodes/launch/game.launch"
    exit 1
fi
print_success "Launch file found"

echo ""
echo "=========================================="
print_info "Launching all ROS nodes..."
echo "=========================================="
echo ""
print_info "This will start:"
echo "  • INFO_USER node (collects user information)"
echo "  • GAME_NODE (main game logic with 3 phases)"
echo "  • RESULT_NODE (displays final results)"
echo "  • CONTROL_NODE (keyboard control with real-time feedback)"
echo "  • GUI nodes (user input, difficulty selection, game window)"
echo ""
print_warning "Press Ctrl+C to stop all nodes"
echo ""

# Final verification before launch
echo ""
print_info "Final verification before launch..."
if rospack find ros_nodes &> /dev/null; then
    ROS_NODES_PATH=$(rospack find ros_nodes)
    print_success "ros_nodes package location: $ROS_NODES_PATH"
else
    print_error "Cannot find ros_nodes package even after setup"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check ROS_PACKAGE_PATH: echo \$ROS_PACKAGE_PATH"
    echo "  2. Try manually: export ROS_PACKAGE_PATH=\$ROS_PACKAGE_PATH:$(pwd)"
    echo "  3. Then: rospack find ros_nodes"
    exit 1
fi

# Launch the nodes
echo ""
print_info "Starting roslaunch..."
roslaunch ros_nodes game.launch

