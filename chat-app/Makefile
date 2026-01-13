# Variables
IMAGE_NAME=flask-frontend
CONTAINER_NAME=flask-app
ENV_FILE=.env
PORT=5000
NETWORK_NAME=agent-network

.PHONY: build build_no_cache run stop clean setup-net

# Create the network so the Flask app can find the Agent by name
setup-net:
	docker network create $(NETWORK_NAME) || true

# Build the Flask image
build:
	docker build -t $(IMAGE_NAME) .

# Build without cache (use if you change requirements.txt)
build_no_cache:
	docker build --no-cache -t $(IMAGE_NAME) .

# Run the Flask app
# We use -v to enable "Hot Reload": changes you make to code update instantly
run: setup-net
	docker run -d \
		--name $(CONTAINER_NAME) \
		--network $(NETWORK_NAME) \
		-p $(PORT):$(PORT) \
		-v $(PWD):/app \
		--env-file $(ENV_FILE) \
		$(IMAGE_NAME)
	@echo "---------------------------------------"
	@echo "Frontend running at: http://localhost:$(PORT)"
	@echo "Looking for Agent at: http://agent-container:8000"
	@echo "---------------------------------------"

# Stop the frontend
stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Check logs (very important for debugging connection errors)
logs:
	docker logs -f $(CONTAINER_NAME)

clean: stop
	docker rmi $(IMAGE_NAME) || true