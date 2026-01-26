pipeline {
    agent any
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }
    stages {
        stage('Cleanup & Checkout') {
            steps {
                cleanWs() 
                echo 'Checking out code from GitHub...'
                git branch: 'main', 
                    credentialsId: 'github-token', 
                    url: 'https://github.com/rubybriggs/Study-Buddy-AI.git'
            }
        }
        
        stage('Verify Docker Hub Repository') {
            steps {
                script {
                    sh """
                    # Check if repository exists before building
                    echo "Verifying Docker Hub repository: ${DOCKER_HUB_REPO}"
                    RESPONSE=\$(curl -s -o /dev/null -w "%{http_code}" "https://hub.docker.com/v2/repositories/${DOCKER_HUB_REPO}/")
                    if [ "\$RESPONSE" != "200" ]; then
                        echo "ERROR: Repository ${DOCKER_HUB_REPO} not found on Docker Hub!"
                        echo "Please create it at: https://hub.docker.com/repository/create"
                        exit 1
                    fi
                    echo "Repository exists. Proceeding..."
                    """
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
                    dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                }
            }
        }
        
        stage('Push Image to DockerHub') {
            steps {
                script {
                    echo 'Pushing Docker image to DockerHub...'
                    docker.withRegistry('https://registry.hub.docker.com', "${DOCKER_HUB_CREDENTIALS_ID}") {
                        dockerImage.push("${IMAGE_TAG}")
                        // Optionally push as latest too
                        dockerImage.push("latest")
                    }
                }
            }
        }
        
        stage('Cleanup Docker Images') {
            steps {
                sh '''
                echo "Cleaning up Docker images..."
                docker rmi ${DOCKER_HUB_REPO}:${IMAGE_TAG} 2>/dev/null || true
                docker system prune -f 2>/dev/null || true
                '''
            }
        }
        
        stage('Update Deployment YAML with New Tag') {
            steps {
                script {
                    echo "Updating deployment.yaml with tag: ${IMAGE_TAG}"
                    sh "sed -i 's|image: rubybriggs/studybuddy:.*|image: rubybriggs/studybuddy:${IMAGE_TAG}|' manifests/deployment.yaml"
                    // Verify the change
                    sh "grep 'image:' manifests/deployment.yaml"
                }
            }
        }
        
        stage('Commit Updated YAML') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs07@gmail.com"
                        git add manifests/deployment.yaml
                        
                        # Check if there are actual changes
                        if git diff --cached --quiet; then
                            echo "No changes to commit"
                        else
                            git commit -m "Update image tag to ${IMAGE_TAG}"
                            git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                        fi
                        '''
                    }
                }
            }
        }
        
        stage('Install Kubectl & ArgoCD CLI Setup') {
            steps {
                sh '''
                echo 'Installing tools locally in workspace...'
                curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                chmod +x kubectl
                
                curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                chmod +x argocd
                '''
            }
        }
        
        stage('Apply Kubernetes & Sync App with ArgoCD') {
            steps {
                script {
                    withKubeConfig([credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443']) {
                        sh '''
                        # Using ./ to reference the local binaries downloaded in the previous stage
                        ./kubectl config use-context minikube
                        echo "Applying Kubernetes manifests..."
                        ./kubectl apply -f manifests/

                        # Getting ArgoCD password from the secret
                        ARGOCD_PWD=$(./kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
                        
                        echo "Logging into ArgoCD..."
                        ./argocd login 34.61.123.87:31704 --username admin --password "${ARGOCD_PWD}" --insecure
                        
                        echo "Syncing application..."
                        ./argocd app sync study --force
                        
                        echo "Waiting for sync to complete..."
                        ./argocd app wait study --health --timeout 180
                        '''
                    }
                }
            }
        }
    }
    
    post {
        failure {
            echo "Pipeline failed! Check the logs above."
            script {
                currentBuild.result = 'FAILURE'
            }
        }
        success {
            echo "Pipeline succeeded!"
            echo "Image pushed: ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
            script {
                currentBuild.result = 'SUCCESS'
            }
        }
        always {
            echo "Pipeline completed with status: ${currentBuild.result}"
            sh 'rm -f kubectl argocd 2>/dev/null || true'
        }
    }
}