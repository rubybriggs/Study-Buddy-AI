pipeline {
    agent any
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // This ensures the workspace is clean BEFORE the auto-checkout happens
        skipDefaultCheckout(false)
    }

    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        // Enabling BuildKit for faster, more stable builds
        DOCKER_BUILDKIT = "1" 
    }

    parameters {
        booleanParam(name: 'SKIP_KUBERNETES', defaultValue: true, description: 'Skip Kubernetes/ArgoCD stage if kubeconfig issues')
    }

    stages {
        stage('Initialize & Clean') {
            steps {
                // Cleaning up old artifacts and images to prevent Disk Space hangs
                sh 'docker system prune -f --filter "until=24h" || true'
                cleanWs()
            }
        }

        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                git branch: 'main', 
                    credentialsId: 'github-token', 
                    url: 'https://github.com/rubybriggs/Study-Buddy-AI.git'
            }
        }
        
        stage('Verify Docker Hub') {
            steps {
                script {
                    sh """
                    RESPONSE=\$(curl -s -o /dev/null -w "%{http_code}" "https://hub.docker.com/v2/repositories/${DOCKER_HUB_REPO}/")
                    if [ "\$RESPONSE" != "200" ]; then
                        echo "ERROR: Repository ${DOCKER_HUB_REPO} not found!"
                        exit 1
                    fi
                    """
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image with BuildKit...'
                    // Added --pull to ensure we have the latest base image and --no-cache to prevent hanging on corrupted layers
                    sh "docker build --pull --no-cache -t ${DOCKER_HUB_REPO}:${IMAGE_TAG} ."
                    sh "docker tag ${DOCKER_HUB_REPO}:${IMAGE_TAG} ${DOCKER_HUB_REPO}:latest"
                }
            }
        }
        
        stage('Push to DockerHub') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', "${DOCKER_HUB_CREDENTIALS_ID}") {
                        sh "docker push ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
                        sh "docker push ${DOCKER_HUB_REPO}:latest"
                    }
                }
            }
        }
        
        stage('Update Manifests') {
            steps {
                script {
                    sh "sed -i 's|image: ${DOCKER_HUB_REPO}:.*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' manifests/deployment.yaml"
                    
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs07@gmail.com"
                        git add manifests/deployment.yaml
                        if ! git diff --cached --quiet; then
                            git commit -m "Update image tag to ${IMAGE_TAG} [skip ci]"
                            git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                        fi
                        '''
                    }
                }
            }
        }

        stage('Deploy (Optional)') {
            when { expression { params.SKIP_KUBERNETES == false } }
            steps {
                script {
                    // Optimized tool download: Check if they exist first
                    sh '''
                    [ -f kubectl ] || curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                    [ -f argocd ] || curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                    chmod +x kubectl argocd
                    '''
                    // ... (Your existing K8s logic remains here)
                }
            }
        }
    }
    
    post {
        always {
            sh 'rm -f kubectl argocd kubeconfig*.yaml 2>/dev/null || true'
        }
    }
}