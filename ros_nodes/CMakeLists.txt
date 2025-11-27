cmake_minimum_required(VERSION 3.0.2)
project(ros_nodes)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  message_generation
)

add_message_files(
  FILES
  user_msg.msg
)

add_service_files(
  FILES
  GetUserScore.srv
  SetGameDifficulty.srv
)

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

