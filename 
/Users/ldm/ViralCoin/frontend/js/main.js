    // Create status message element if it doesn't exist
    deploymentProgress = document.getElementById('deploymentProgress');
    if (!deploymentProgress) {
        deploymentProgress = document.createElement('div');
        deploymentProgress.id = 'deploymentProgress';
        deploymentProgress.className = 'deployment-progress card p-3 mb-4';
        deploymentProgress.innerHTML = `
            <h5 class="card-title text-center mb-3">Token Deployment Process</h5>
            <div class="progress mb-3">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" role="progressbar" style="width: 0%"></div>
            </div>
            <div class="d-flex align-items-center mb-3">
                <div class="step-icon me-3 bg-primary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                    <i class="fas fa-cog"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="current-step fw-bold">Initializing...</div>
                    <div class="step-details small text-muted"></div>
                </div>
                <div class="step-percentage fw-bold text-primary">0%</div>
            </div>
            <div class="deployment-stages">
                <div class="step-timeline">
                    <div class="timeline-container">
                        ${progressSteps.map(step => `
                            <div class="timeline-step" data-step="${step.id}">
                                <div class="timeline-marker"></div>
                                <small class="timeline-label">${step.label}</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            <div class="token-result mt-3" style="display: none;"></div>
        `;
    // Function to update progress with enhanced visualization
    const updateProgress = (stepId, additionalInfo = '') => {
        const step = progressSteps.find(s => s.id === stepId);
        
        // Exit if no valid step found
        if (!step) return;
        
        const progressBar = deploymentProgress.querySelector('.progress-bar');
        const currentStep = deploymentProgress.querySelector('.current-step');
        const stepDetails = deploymentProgress.querySelector('.step-details');
        const stepIcon = deploymentProgress.querySelector('.step-icon i');
        const stepPercentage = deploymentProgress.querySelector('.step-percentage');
        
        // Update progress bar
        if (progressBar) {
            progressBar.style.width = `${step.pct}%`;
            progressBar.setAttribute('aria-valuenow', step.pct);
        }
        
        // Update step information
        if (currentStep) currentStep.textContent = step.label;
        if (stepDetails) {
            if (additionalInfo) {
                stepDetails.textContent = additionalInfo;
                stepDetails.style.display = 'block';
            } else {
                stepDetails.style.display = 'none';
            }
        }
        
        // Update icon
        if (stepIcon && step.icon) {
            stepIcon.className = `fas ${step.icon}`;
        }
        
        // Update percentage
        if (stepPercentage) {
            stepPercentage.textContent = `${step.pct}%`;
        }
        
        // Update timeline display
        const timelineSteps = deploymentProgress.querySelectorAll('.timeline-step');
        if (timelineSteps && timelineSteps.length) {
            timelineSteps.forEach(timelineStep => {
                const timelineStepId = timelineStep.getAttribute('data-step');
                const timelineMarker = timelineStep.querySelector('.timeline-marker');
                const timelineStepObj = progressSteps.find(s => s.id === timelineStepId);
                
                if (timelineStepObj && timelineMarker) {
                    // Mark previous steps as completed
                    if (timelineStepObj.pct < step.pct) {
                        timelineMarker.classList.add('completed');
                    } 
                    // Mark current step as active
                    else if (timelineStepObj.id === step.id) {
                        timelineMarker.classList.add('active');
                    }
                }
            });
        }
        
        console.log(`Deployment progress: ${step.label} (${step.pct}%)`);
            // Simulate successful deployment
            updateProgress('complete', `Token created at address: ${tokenAddress}`);
            
            // Get explorer URLs for the token
            const networkData = SUPPORTED_NETWORKS[currentChainId] || SUPPORTED_NETWORKS[80001]; // Default to Mumbai
            const explorerUrl = `${networkData.blockExplorer}/address/${tokenAddress}`;
            
            // Show the deployment result
            const tokenResult = deploymentProgress.querySelector('.token-result');
            if (tokenResult) {
                tokenResult.style.display = 'block';
                tokenResult.innerHTML = `
                    <div class="token-deployment-success bg-light rounded p-3">
                        <div class="text-center mb-3">
                            <span class="deployment-success-icon d-inline-block mb-2">
                                <i class="fas fa-check-circle text-success fa-3x pulse-animation"></i>
                            </span>
                            <h5 class="text-success">Token Created Successfully!</h5>
                        </div>
                        <div class="token-info-card border rounded p-3 mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="fw-bold">Token Name:</span>
                                <span>${name}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="fw-bold">Token Symbol:</span>
                                <span>${symbol}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="fw-bol
