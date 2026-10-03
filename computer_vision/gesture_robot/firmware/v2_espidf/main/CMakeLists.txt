idf_component_register(
    SRCS "app_main.cpp" "at_client.cpp"
    INCLUDE_DIRS "."
    REQUIRES esp_driver_uart esp_timer json
)
