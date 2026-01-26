pipeline {
    agent any
    environment {
        DOCKER_HUB_REPO = "rubybriggs/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }
    stages {
        stage('System Health Check') {
            steps {
                sh '''
                echo "--- Checking Server Resources ---"
                df -h /var/jenkins_home || true
                free -m || true
                docker system df || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // This uses the Docker pipeline plugin
                    // It will look for the Dockerfile in your root directory
                    dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                }
            }
        }

        stage('Push Image to DockerHub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', "${DOCKER_HUB_CREDENTIALS_ID}") {
                        dockerImage.push("${IMAGE_TAG}")
                        dockerImage.push("latest")
                    }
                }
            }
        }

        stage('Update Manifests') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh """
                        # Update the deployment file
                        sed -i 's|image: ${DOCKER_HUB_REPO}:.*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' manifests/deployment.yaml
                        
                        # Git Configuration
                        git config user.name "rubybriggs"
                        git config user.email "rubybriggs07@gmail.com"
                        
                        # Commit and Push with [skip ci] to avoid infinite loops
                        git add manifests/deployment.yaml
                        if git diff --quiet && git diff --staged --quiet; then
                            echo "No changes to commit"
                        else
                            git commit -m "chore: update image tag to ${IMAGE_TAG} [skip ci]"
                            git push https://${GIT_USER}:${GIT_PASS}@github.com/rubybriggs/Study-Buddy-AI.git HEAD:main
                        fi
                        """
                    }
                }
            }
        }

        stage('Sync ArgoCD') {
            steps {
                script {
                    // This block ensures kubectl has the right context before running Argo commands
                    kubeconfig(credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443') {
                        sh '''
                        echo "Logging into ArgoCD..."
                        ARGOCD_PASS=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
                        argocd login 34.61.123.87:31704 --username admin --password $ARGOCD_PASS --insecure
                        
                        echo "Syncing Application..."
                        argocd app sync study --force
                        '''
                    }
                }
            }
        }
    }
    
    post {
        failure {
            echo "Pipeline failed. Check the Health Check stage and Docker logs."
        }
        success {
            echo "Pipeline completed successfully. Image ${IMAGE_TAG} is now live."
        }
    }
}