// ./assets/js/booking-system.js

const state = {
    currentStep: 1,
    selectedService: null,
    selectedDate: null,
    selectedTime: null,
    services: {
        'corte': { name: 'Corte de Cabelo', duration: 45 },
        'escova': { name: 'Escova Simples', duration: 30 },
        'manicure': { name: 'Manicure + Pedicure', duration: 60 },
        'coloracao': { name: 'Coloração', duration: 90 }
    },
    // Simulação de horários indisponíveis (como se já tivessem sido agendados)
    // Formato: 'YYYY-MM-DD': ['HH:MM', 'HH:MM']
    unavailableTimes: {
        '2025-11-20': ['10:00', '11:30'],
        '2025-11-21': ['14:00']
    },
    // Configuração de funcionamento do salão
    openingTime: 9 * 60, // 09:00 em minutos (9 * 60)
    closingTime: 18 * 60, // 18:00 em minutos (18 * 60)
    interval: 30 // Intervalo de agendamento em minutos
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Configura a data mínima no input para hoje
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date-input').min = today;

    // 2. Adiciona listeners de eventos
    document.getElementById('service-select').addEventListener('change', handleServiceChange);
    document.getElementById('date-input').addEventListener('change', handleDateChange);
    document.getElementById('client-name').addEventListener('input', checkStep3Validity); // Listener para validação de nome
    document.getElementById('booking-form').addEventListener('submit', submitBooking);

    // 3. Inicializa o estado visual
    updateStepDisplay();
});

/**
 * Funções de Navegação e Controle de Passo
 */
function updateStepDisplay() {
    document.querySelectorAll('.booking-step').forEach(step => {
        step.classList.remove('active');
    });
    const activeStepElement = document.getElementById(`step-${state.currentStep}`);
    if (activeStepElement) {
        activeStepElement.classList.add('active');
    }
}

function nextStep(step) {
    state.currentStep = step;
    updateStepDisplay();
}

function prevStep(step) {
    state.currentStep = step;
    updateStepDisplay();
}

function resetBooking() {
    state.currentStep = 1;
    state.selectedService = null;
    state.selectedDate = null;
    state.selectedTime = null;
    document.getElementById('booking-form').reset();
    document.getElementById('time-slots').innerHTML = '<p>Selecione uma data para ver os horários disponíveis.</p>';
    updateStepDisplay();
}

/**
 * Funções de Validação e Dados
 */
function handleServiceChange(event) {
    const serviceKey = event.target.value;
    state.selectedService = state.services[serviceKey];
    document.getElementById('next-step-1').disabled = !state.selectedService;
}

function handleDateChange(event) {
    state.selectedDate = event.target.value;
    document.getElementById('next-step-2').disabled = true;
    state.selectedTime = null; // Reseta a hora ao mudar a data
    generateTimeSlots(state.selectedDate);
}

function generateTimeSlots(dateString) {
    const slotsContainer = document.getElementById('time-slots');
    slotsContainer.innerHTML = '';
    
    if (!state.selectedService) {
        slotsContainer.innerHTML = '<p>Selecione um serviço primeiro.</p>';
        return;
    }

    const today = new Date().toISOString().split('T')[0];
    const isToday = dateString === today;
    const nowMinutes = isToday ? (new Date().getHours() * 60 + new Date().getMinutes()) : 0;
    
    let time = state.openingTime;
    const duration = state.selectedService.duration;
    const availableTimes = state.unavailableTimes[dateString] || [];
    let hasSlots = false;

    // Cabeçalho da área de horários
    const timeHeader = document.createElement('h3');
    timeHeader.textContent = 'Horários Disponíveis (Clique para selecionar)';
    slotsContainer.appendChild(timeHeader);

    const grid = document.createElement('div');
    grid.classList.add('time-grid');

    while (time + duration <= state.closingTime) {
        const hour = Math.floor(time / 60).toString().padStart(2, '0');
        const minute = (time % 60).toString().padStart(2, '0');
        const slot = `${hour}:${minute}`;
        
        // Verifica se o slot já passou (se for hoje)
        const slotMinutes = time;
        if (isToday && slotMinutes < nowMinutes) {
            time += state.interval;
            continue;
        }

        // Verifica indisponibilidade (simulação simples)
        if (!availableTimes.includes(slot)) {
            const button = document.createElement('button');
            button.type = 'button';
            button.classList.add('time-slot-btn');
            button.textContent = slot;
            button.dataset.time = slot;
            button.addEventListener('click', selectTimeSlot);
            grid.appendChild(button);
            hasSlots = true;
        }
        
        time += state.interval;
    }
    
    slotsContainer.appendChild(grid);

    if (!hasSlots) {
        slotsContainer.innerHTML = '<p class="no-slots-message">Nenhum horário disponível nesta data. Tente outra.</p>';
    }
}

function selectTimeSlot(event) {
    // Remove a classe 'selected' de todos os botões de horário
    document.querySelectorAll('.time-slot-btn').forEach(btn => {
        btn.classList.remove('selected');
    });

    // Adiciona a classe 'selected' ao botão clicado
    event.target.classList.add('selected');
    state.selectedTime = event.target.dataset.time;
    
    // Habilita o botão de "Próximo"
    document.getElementById('next-step-2').disabled = false;
    
    // Atualiza o resumo
    updateSummary();
}

function updateSummary() {
    if (state.selectedService && state.selectedDate && state.selectedTime) {
        document.getElementById('summary-service').textContent = state.selectedService.name;
        
        // Formata a data para visualização (DD/MM/YYYY)
        const [year, month, day] = state.selectedDate.split('-');
        document.getElementById('summary-date').textContent = `${day}/${month}/${year}`;
        
        document.getElementById('summary-time').textContent = state.selectedTime;
    }
    checkStep3Validity(); // Garante que o botão de submit está correto
}

function checkStep3Validity() {
    const nameInput = document.getElementById('client-name');
    const submitButton = document.getElementById('submit-booking');
    
    // VERIFICAÇÃO APERFEIÇOADA:
    // 1. Garante que o nome não é vazio e não é apenas espaços em branco (trim().length > 0)
    const isNameValid = nameInput.value.trim().length > 0;
    // 2. Garante que a reserva (serviço, data e hora) está completa
    const isBookingReady = state.selectedService && state.selectedDate && state.selectedTime;
    
    // O botão só fica ativo se AMBAS as condições forem verdadeiras
    submitButton.disabled = !(isNameValid && isBookingReady);
}

/**
 * Funções de Envio
 */
function submitBooking(event) {
    event.preventDefault(); // Impede o envio padrão do formulário
    
    const clientName = document.getElementById('client-name').value;
    const clientWhatsapp = document.getElementById('client-whatsapp').value;
    
    const serviceName = state.selectedService.name;
    const dateFormatted = document.getElementById('summary-date').textContent;
    const timeFormatted = state.selectedTime;
    
    // Texto da mensagem a ser enviada pelo WhatsApp
    const whatsappMessage = 
        `Olá Kamila Lima! Gostaria de confirmar meu agendamento com os seguintes dados:\n\n` +
        `💅 Serviço: *${serviceName}*\n` +
        `🗓 Data: *${dateFormatted}*\n` +
        `⏰ Horário: *${timeFormatted}*\n` +
        `👤 Cliente: *${clientName}*\n` +
        `\nObrigado!`;
    
    // Número de telefone da Kamila Lima
    const whatsappLink = 
        `https://api.whatsapp.com/send?phone=5582988334997&text=${encodeURIComponent(whatsappMessage)}`;

    // Exibe a mensagem de sucesso
    document.querySelectorAll('.booking-step').forEach(step => step.classList.remove('active'));
    document.getElementById('confirmation-message').classList.add('active');
    
    // Redireciona para o WhatsApp após um pequeno atraso
    setTimeout(() => {
        window.open(whatsappLink, '_blank');
    }, 1500); // 1.5 segundos de atraso para o usuário ver a confirmação

    // O agendamento real (e a atualização do unavailableTimes) exigiria um Backend.
    // Esta é a solução de "agendamento por WhatsApp" (Frontend puro).
}