idf_component_register(
    SRCS "app_main.cpp" "at_client.cpp" "ros_link.cpp" "gesture_debouncer.cpp"
    INCLUDE_DIRS "."
    REQUIRES esp_driver_uart esp_timer json micro_ros_espidf_component
)
