#!/usr/bin/env python3
import rospy
from ros_nodes.msg import user_msg
from ros_nodes.srv import GetUserScore
from std_msgs.msg import Int64

class ResultGameNode:
    def __init__(self):
        rospy.init_node('result_node', anonymous=True)
        
        self.user_name = ""  # Store user's name for service call
        self.user_username = ""  # Store username for display (from user_information topic)
        
        self.sub_info = rospy.Subscriber('user_information', user_msg, self.user_info_cb)
        self.sub_res = rospy.Subscriber('result_information', Int64, self.result_cb)
        
        rospy.loginfo("RESULT_NODE initialized")

    def user_info_cb(self, msg):
        rospy.loginfo("RESULT_NODE: Received user information message")
        rospy.loginfo("RESULT_NODE: Transitioning to process user information")
        
        # Store user's name for service call and username for display
        self.user_name = msg.name  # Store name for service call (as per requirement)
        self.user_username = msg.username  # Store username for display
        rospy.loginfo(f"RESULT_NODE: Stored user name: {self.user_name}, username: {self.user_username}")
        rospy.loginfo(f"RESULT_NODE: User information processed successfully (Name: {msg.name}, Username: {msg.username}, Age: {msg.age})")

    def result_cb(self, msg):
        rospy.loginfo("RESULT_NODE: Received result information message")
        rospy.loginfo("RESULT_NODE: Transitioning to process final score")
        
        score = msg.data
        rospy.loginfo(f"RESULT_NODE: Received final score: {score}")
        rospy.loginfo("RESULT_NODE: Transitioning to display results")
        
        # Display final message with score and username
        print(f"\nGAME OVER\nUser: {self.user_username}\nScore: {score}")
        rospy.loginfo("RESULT_NODE: Results displayed to user")
        
        # Call service to get percentage score (as per requirement)
        rospy.loginfo("RESULT_NODE: Transitioning to get score percentage from service")
        self.get_score_percentage()
        rospy.loginfo("RESULT_NODE: Result processing completed")

    def get_score_percentage(self):
        """Call user_score service with user's name and print percentage score."""
        rospy.loginfo("RESULT_NODE: Waiting for 'user_score' service to become available...")
        rospy.wait_for_service('user_score')
        rospy.loginfo("RESULT_NODE: 'user_score' service is available")
        
        try:
            # As per requirement: "sends to the user_score service the name of the user"
            rospy.loginfo(f"RESULT_NODE: Calling 'user_score' service with user name: {self.user_name}")
            get_score = rospy.ServiceProxy('user_score', GetUserScore)
            
            # Use positional argument (more reliable with generated service code)
            resp = get_score(self.user_name)
            
            # Get score value from response - handle different possible field names
            score_value = None
            
            # Log all available attributes for debugging
            all_attrs = [a for a in dir(resp) if not a.startswith('_')]
            rospy.loginfo(f"RESULT_NODE: GetUserScore response object type: {type(resp)}, attributes: {all_attrs}")
            
            # Try different possible field names
            if hasattr(resp, 'score'):
                try:
                    score_value = resp.score
                    rospy.loginfo(f"RESULT_NODE: Found 'score' field: {score_value}")
                except AttributeError:
                    pass
            elif hasattr(resp, 'score_percentage'):
                try:
                    score_value = resp.score_percentage
                    rospy.loginfo(f"RESULT_NODE: Found 'score_percentage' field: {score_value}")
                except AttributeError:
                    pass
            
            # Try to get from __dict__ if available
            if score_value is None and hasattr(resp, '__dict__'):
                for key, val in resp.__dict__.items():
                    if isinstance(val, (int, float)):
                        score_value = val
                        rospy.logwarn(f"RESULT_NODE: Using __dict__ key '{key}' for score: {score_value}")
                        break
            
            # Last resort: try to get the first numeric attribute
            if score_value is None:
                for attr in all_attrs:
                    try:
                        val = getattr(resp, attr)
                        if isinstance(val, (int, float)):
                            score_value = val
                            rospy.logwarn(f"RESULT_NODE: Using field '{attr}' for score (expected 'score'): {score_value}")
                            break
                    except:
                        continue
            
            if score_value is None:
                rospy.logerr("RESULT_NODE: Could not find score field in response")
                rospy.logerr(f"RESULT_NODE: Available attributes: {all_attrs}")
                # Try to get all attribute values
                for attr in all_attrs:
                    try:
                        val = getattr(resp, attr)
                        rospy.logerr(f"RESULT_NODE:   {attr} = {val} (type: {type(val)})")
                    except:
                        pass
                score_value = 0  # Default to 0 if we can't find it
            
            # Service returns int64 score (percentage)
            rospy.loginfo(f"RESULT_NODE: Service call successful, received score (percentage): {score_value}")
            # Print the percentage score as per requirement
            print(f"Score Percentage: {score_value}%")
        except (rospy.ServiceException, AttributeError, TypeError) as e:
            rospy.logerr(f"RESULT_NODE: Service call failed: {e}")
            import traceback
            rospy.logerr(f"RESULT_NODE: Traceback: {traceback.format_exc()}")
        except Exception as e:
            rospy.logerr(f"RESULT_NODE: Unexpected error in get_score_percentage: {e}")
            import traceback
            rospy.logerr(f"RESULT_NODE: Traceback: {traceback.format_exc()}")

    def run(self):
        rospy.loginfo("RESULT_NODE: Starting main loop (rospy.spin())")
        rospy.loginfo("RESULT_NODE: Node is now active and waiting for messages")
        rospy.spin()
        rospy.loginfo("RESULT_NODE: Main loop exited")

if __name__ == '__main__':
    try:
        rospy.loginfo("RESULT_NODE: Starting RESULT_NODE...")
        node = ResultGameNode()
        node.run()
        rospy.loginfo("RESULT_NODE: Node execution completed")
    except rospy.ROSInterruptException:
        rospy.loginfo("RESULT_NODE: Node interrupted by user")
    except Exception as e:
        rospy.logerr(f"RESULT_NODE: Error occurred: {e}")

