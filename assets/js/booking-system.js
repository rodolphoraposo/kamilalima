// ./assets/js/booking-system.js

// ⚠️ ATENÇÃO: Defina a URL base da sua API. Para desenvolvimento local, use:
const API_BASE_URL = 'http://127.0.0.1:5000/api'; 
// Para produção (após o deploy), você usará a URL do Render/Vercel.

const state = {
    currentStep: 1,
    selectedService: null,
    selectedDate: null,
    selectedTime: null,
    services: {}, // Será preenchido pela API
    unavailableTimes: [], // Será preenchido pela API
    
    // Configuração de funcionamento do salão (pode ser hardcoded ou vir da API no futuro)
    openingTime: 9 * 60, // 09:00 em minutos
    closingTime: 18 * 60, // 18:00 em minutos
    interval: 30 // Intervalo de agendamento em minutos
};

/**
 * Funções Auxiliares
 */

// Função auxiliar para converter HH:MM ou HH:MM:SS em minutos
function timeToMinutes(timeString) {
    const parts = timeString.substring(0, 5).split(':');
    const h = Number(parts[0]);
    const m = Number(parts[1]);
    return h * 60 + m;
}

/**
 * Funções de Comunicação com a API (RE-IMPLEMENTADAS)
 */

async function fetchServices() {
    try {
        const response = await fetch(`${API_BASE_URL}/servicos`);
        if (!response.ok) {
            throw new Error('Falha ao buscar serviços da API');
        }
        const data = await response.json();

        // Limpa o select e o state.services
        state.services = {};
        const select = document.getElementById('service-select');
        select.innerHTML = '<option value="">Selecione um Serviço</option>';

        data.forEach(service => {
            // Usa o ID para comunicação com o backend e o nome para exibição
            const key = service.id; 
            state.services[key] = {
                id: service.id,
                name: service.nome,
                duration: service.duracao_minutos,
                price: service.preco
            };
            const option = document.createElement('option');
            option.value = key;
            option.textContent = `${service.nome} (R$ ${service.preco.toFixed(2)} - ${service.duracao_minutos} min)`;
            select.appendChild(option);
        });
        console.log('Serviços carregados:', state.services);

    } catch (error) {
        console.error('Erro ao buscar serviços:', error);
        alert('Não foi possível carregar os serviços. Verifique a conexão com o Backend.');
    }
}


async function fetchUnavailableTimes() {
    try {
        const response = await fetch(`${API_BASE_URL}/horarios-indisponiveis`);
        if (!response.ok) {
            throw new Error('Falha ao buscar horários indisponíveis');
        }
        const data = await response.json();
        
        // Converte os horários de início e fim para minutos
        state.unavailableTimes = data.map(item => ({
            date: item.data,
            startMinutes: timeToMinutes(item.hora_inicio),
            endMinutes: timeToMinutes(item.hora_fim)
        }));
        console.log('Horários indisponíveis carregados:', state.unavailableTimes);

    } catch (error) {
        console.error('Erro ao buscar horários ocupados:', error);
    }
}

/**
 * Funções de Validação e Dados
 */

function isSlotOccupied(startMinutes, serviceDuration, dateString) {
    const endMinutes = startMinutes + serviceDuration;

    return state.unavailableTimes.some(booking => {
        // 1. Deve ser o mesmo dia
        if (booking.date !== dateString) {
            return false;
        }

        // 2. Verifica sobreposição: O novo agendamento (startMinutes a endMinutes)
        // se sobrepõe ao agendamento existente (booking.startMinutes a booking.endMinutes)
        // A regra é: se o novo agendamento começar ANTES do final do existente E
        // terminar DEPOIS do início do existente, há sobreposição.
        return startMinutes < booking.endMinutes && endMinutes > booking.startMinutes;
    });
}

function handleServiceChange(event) {
    const serviceId = event.target.value;
    state.selectedService = state.services[serviceId];
    document.getElementById('next-step-1').disabled = !state.selectedService;
    if(state.selectedDate) {
        generateTimeSlots(state.selectedDate);
    }
}

// 🛑 FUNÇÃO CHAVE: COM LÓGICA DE VERIFICAÇÃO DE OCUAPÇÃO DO BD
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
    const serviceDuration = state.selectedService.duration;
    
    let hasSlots = false;

    const timeHeader = document.createElement('h3');
    timeHeader.textContent = `Horários Disponíveis (Duração: ${serviceDuration} min)`;
    slotsContainer.appendChild(timeHeader);

    const grid = document.createElement('div');
    grid.classList.add('time-grid');

    while (time + state.interval <= state.closingTime) { 
        const startMinutes = time;
        const endMinutes = time + serviceDuration; // Fim do NOVO agendamento
        
        const hour = Math.floor(startMinutes / 60).toString().padStart(2, '0');
        const minute = (startMinutes % 60).toString().padStart(2, '0');
        const slot = `${hour}:${minute}`;
        
        // 1. Verifica se o slot já passou (se for hoje)
        if (isToday && startMinutes < nowMinutes) {
            time += state.interval;
            continue;
        }

        // 2. Verifica se o serviço cabe antes do fechamento
        if (endMinutes > state.closingTime) {
             time += state.interval;
             continue; 
        }
        
        // 3. ⚠️ IMPLEMENTAÇÃO DA VERIFICAÇÃO DE SOBREPOSIÇÃO DO BD
        let isOccupied = isSlotOccupied(startMinutes, serviceDuration, dateString);

        if (!isOccupied) {
            const button = document.createElement('button');
            button.type = 'button';
            button.classList.add('time-slot-btn');
            button.textContent = slot;
            button.dataset.time = slot;
            button.addEventListener('click', selectTimeSlot);
            grid.appendChild(button);
            hasSlots = true;
        }
        
        time += state.interval; // Passa para o próximo intervalo (30 minutos)
    }
    
    slotsContainer.appendChild(grid);

    if (!hasSlots && slotsContainer.children.length === 1) { 
        slotsContainer.innerHTML = '<p class="no-slots-message">Nenhum horário disponível nesta data. Tente outra.</p>';
    }
}


function selectTimeSlot(event) {
    document.querySelectorAll('.time-slot-btn').forEach(btn => {
        btn.classList.remove('selected');
    });

    event.target.classList.add('selected');
    state.selectedTime = event.target.dataset.time;
    
    document.getElementById('next-step-2').disabled = false;
    
    updateSummary();
}

function updateSummary() {
    if (state.selectedService && state.selectedDate && state.selectedTime) {
        document.getElementById('summary-service').textContent = state.selectedService.name;
        
        const [year, month, day] = state.selectedDate.split('-');
        document.getElementById('summary-date').textContent = `${day}/${month}/${year}`;
        
        document.getElementById('summary-time').textContent = state.selectedTime;
    }
    checkStep3Validity(); 
}

function checkStep3Validity() {
    const nameInput = document.getElementById('client-name');
    const submitButton = document.getElementById('submit-booking');
    
    const isNameValid = nameInput.value.trim().length > 0;
    const isBookingReady = state.selectedService && state.selectedDate && state.selectedTime;
    
    submitButton.disabled = !(isNameValid && isBookingReady);
}

/**
 * Funções de Envio (RE-IMPLEMENTADA PARA API REST)
 */
async function submitBooking(event) {
    event.preventDefault(); 
    
    document.getElementById('submit-booking').disabled = true;

    const clientName = document.getElementById('client-name').value.trim();
    const clientWhatsapp = document.getElementById('client-whatsapp').value.trim();
    
    const service = state.selectedService;
    const horaInicio = state.selectedTime;
    
    // Cálculo da hora final do serviço para enviar ao Backend
    const startMinutes = timeToMinutes(horaInicio);
    const endMinutes = startMinutes + service.duration;
    
    const horaFim = 
        `${Math.floor(endMinutes / 60).toString().padStart(2, '0')}:${(endMinutes % 60).toString().padStart(2, '0')}:00`;

    // 1. Estrutura de dados para o Backend
    const bookingData = {
        cliente_nome: clientName,
        cliente_whatsapp: clientWhatsapp,
        servico_nome: service.name, // O backend buscará o servico_id pelo nome
        data_agendamento: state.selectedDate,
        hora_inicio: horaInicio + ":00", // Adiciona segundos para formato MySQL
        hora_fim: horaFim
    };
    
    // 2. Envio para a API (POST /api/agendamentos)
    try {
        const response = await fetch(`${API_BASE_URL}/agendamentos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData)
        });

        const result = await response.json();
        
        document.querySelectorAll('.booking-step').forEach(step => step.classList.remove('active'));
        const confirmationElement = document.getElementById('confirmation-message');

        if (response.ok) {
            // Sucesso (Status 201)
            confirmationElement.innerHTML = `
                <div class="alert success">
                    <h2>✅ Sucesso!</h2>
                    <p>Agendamento solicitado com sucesso (ID: ${result.id}).</p>
                    <p>Seu horário (${horaInicio}) está *PENDENTE* de aprovação.</p>
                    <p>Você será notificado pelo WhatsApp. Obrigado!</p>
                </div>
                <button onclick="resetBooking()" class="btn-primary">Novo Agendamento</button>
            `;
            // ⚠️ Opcional: Redirecionar para o WhatsApp com a mensagem de agendamento PENDENTE
        } else {
            // Erro do Servidor (Status 400, 500, etc.)
             confirmationElement.innerHTML = `
                <div class="alert error">
                    <h2>❌ Erro ao Agendar!</h2>
                    <p>Não foi possível completar a solicitação.</p>
                    <p>Mensagem: ${result.erro || 'Erro desconhecido.'}</p>
                </div>
                <button onclick="resetBooking()" class="btn-primary">Tentar Novamente</button>
            `;
        }
        
        confirmationElement.classList.add('active');


    } catch (error) {
        console.error('Erro de rede/conexão:', error);
        alert('Erro de conexão com o servidor. Tente novamente mais tarde.');
        document.getElementById('submit-booking').disabled = false; // Reabilita o botão
    }
    
}


// --- FUNÇÃO DE INICIALIZAÇÃO DO SCRIPT ---
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Configura a data mínima no input para hoje
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date-input').min = today;

    // 2. BUSCA DE DADOS NO BACKEND
    await fetchServices();
    await fetchUnavailableTimes();

    // 3. Adiciona listeners de eventos
    document.getElementById('service-select').addEventListener('change', handleServiceChange);
    document.getElementById('date-input').addEventListener('change', handleDateChange);
    document.getElementById('client-name').addEventListener('input', checkStep3Validity); 
    document.getElementById('booking-form').addEventListener('submit', submitBooking);

    // 4. Inicializa o estado visual
    updateStepDisplay();
});


// Funções de Navegação (MANTIDAS)
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
    document.getElementById('next-step-1').disabled = true; 
    document.getElementById('next-step-2').disabled = true; 
    document.getElementById('confirmation-message').classList.remove('active');
    document.getElementById('submit-booking').disabled = true; // Garante que o botão comece desabilitado
    updateStepDisplay();
}