IMAGE_NAME=gemini-agent
CONTAINER_NAME=agent-container
ENV_FILE=.env
PORT=8000
NETWORK_NAME=agent-network

.PHONY: build build_no_cache run stop clean setup-net

# Create the network if it doesn't exist
setup-net:
	docker network create $(NETWORK_NAME) || true

# Build the image
build:
	docker build -t $(IMAGE_NAME) .

# Build the image (no cache)
build_no_cache:
	docker build --no-cache -t $(IMAGE_NAME) .

# Run the container attached to the custom network
run: setup-net
	docker run -d \
		--name $(CONTAINER_NAME) \
		--network $(NETWORK_NAME) \
		-p $(PORT):$(PORT) \
		--env-file $(ENV_FILE) \
		$(IMAGE_NAME)
	@echo "---------------------------------------"
	@echo "App: http://localhost:$(PORT)"
	@echo "Network: $(NETWORK_NAME)"
	@echo "Container Name (DNS): $(CONTAINER_NAME)"
	@echo "Internal IP: " 
	@docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(CONTAINER_NAME)
	@echo "---------------------------------------"

stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

clean: stop
	docker rmi $(IMAGE_NAME) || true
	# Optional: uncomment to remove network on clean
	# docker network rm $(NETWORK_NAME) || true