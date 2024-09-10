import uvicorn


def main():
    uvicorn.run("mpm_input_preprocessing.http.api:api", host="0.0.0.0", port=8080, log_config="logging.yaml", root_path="", reload=True)


if __name__ == "__main__":
    main()
