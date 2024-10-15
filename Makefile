VERSION := 0.0.1

# make helpers
null  :=
space := $(null) #
comma := ,

DETECTED_OS := $(shell uname)


# (╯°□°）╯︵ ┻━┻
ifeq ($(DETECTED_OS),Darwin)
	SED=gsed
else
	SED=sed
endif
# ┬─┬ノ(ಠ_ಠノ)


.DEFAULT_GOAL := help

.PHONY: yN
yN:
	@echo "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ] || (echo "aborted."; exit 1;)

tool-exists-%:
	@which $* > /dev/null

check-%:
	@: $(if $(value $*),,$(error $* is undefined))


help:
	@echo ""
	@echo "By default make targets assume DEV to run production pass in prod=y as a command line argument"
	@echo ""
	@echo "Targets:"
	@echo ""
	@grep -E '^([a-zA-Z_-])+%*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'


.PHONY: print-version
print-version:  ## Print current version
	@printf "${VERSION}"


.PHONY: gitlab-docker-login
gitlab-docker-login:| check-GITLAB_USER check-GITLAB_PASS
	@printf "${GITLAB_PASS}\n" | docker login registry.gitlab.com/jataware -u "${GITLAB_USER}" --password-stdin

.PHONY: docker-build-mpm-api
docker-build-mpm-api:
	(docker build -t mpm_input_preprocessing:dev .)


.PHONY: docker_buildx-mpm-api
docker_buildx-mpm-api:| gitlab-docker-login check-VERSION ## build and push cdr api
	@echo "building mpm-api"
	(docker buildx build \
		--platform linux/amd64 \
		-t registry.gitlab.com/jataware/mpm/api:${VERSION} \
		--output type=image,push=true \
		--progress=plain \
		-f Dockerfile \
		.)