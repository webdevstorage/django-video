from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from .models import Hall, Video
from .forms import VideoForm, SearchForm
from django.http import Http404, JsonResponse
from django.forms.utils import ErrorList
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import urllib
import requests


YOUTUBE_API_KEY = 'AIzaSyAXXXXXXXXXXXXXXXXXX'

def home(request):
    recent_halls = Hall.objects.all().order_by('-id')[:3]
    popular_halls = []
    return render(request, 'halls/home.html', {'recent_halls': recent_halls, 'popular_halls': popular_halls})

@login_required
def dashboard(request):
    halls = Hall.objects.filter(user=request.user)
    return render(request, 'halls/dashboard.html', {'halls': halls})

@login_required
def video_search(request):
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(search_form.cleaned_data['search_term'])
        response = requests.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={ encoded_search_term }&key={ YOUTUBE_API_KEY }')
        return JsonResponse(response.json())
    return JsonResponse({ 'error': 'not able to validate form' })

@login_required
def add_video(request, pk):
    form = VideoForm()
    search_form = SearchForm()
    # find hall object based on url parameter (pk)
    hall = Hall.objects.get(pk=pk)
    # check if requesting user matches username found in hall object. if not, send them to 404.
    if not hall.user == request.user:
        raise Http404
    if request.method == 'POST':
        # VideoForm will take all POST data and assign it to filled_form
        form = VideoForm(request.POST)
        if form.is_valid():
            # if form has valid info, assign 'video' variable to 'Video' model
            video = Video()
            video.hall = hall
            # get form's submitted data using cleaned_data[] method
            video.url = form.cleaned_data['url']
            parsed_url = urllib.parse.urlparse(video.url)
            # getting youtube id in url... v=
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v')
            if video_id:
                video.youtube_id = video_id[0]
                response = requests.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={ video_id[0] }&key={ YOUTUBE_API_KEY }')
                json = response.json()
                # this is how you go down in json object structure... just like props.items.property
                title = json['items'][0]['snippet']['title']
                
                video.title = title
                video.save()
                return redirect('detail_hall', pk)
                #throw error if youtube URL doesn't exist
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('Needs to be a YouTube URL')

    return render(request, 'halls/add_video.html', {'form': form, 'search_form': search_form, 'hall': hall })

class DeleteVideo(LoginRequiredMixin, generic.DeleteView):
    model = Video
    template_name = 'halls/delete_video.html'
    success_url = reverse_lazy('dashboard')

    # check if user actually created the video....
    def get_object(self):
        video = super(DeleteVideo, self).get_object()
        if not video.hall.user == self.request.user:
            raise Http404
        return video

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view

# def create_hall(request):
#    if request.method == 'POST':
        # get the form data
        # validate form data
        # create hall
        # save hall
#    else:
        # create a form for a hall
        # return the template    


#### This class-based view will replace above function-based view!
#### It can be extremely simple.... 

class CreateHall(LoginRequiredMixin, generic.CreateView):
    model = Hall
    fields = ['title']
    template_name = 'halls/create_hall.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreateHall, self).form_valid(form)
        return redirect('dashboard')

class DetailHall(generic.DetailView):
    model = Hall
    template_name = 'halls/detail_hall.html'

class UpdateHall(LoginRequiredMixin, generic.UpdateView):
    model = Hall
    template_name = 'halls/update_hall.html'
    # field which users are allowed to update!
    fields = ['title']
    success_url = reverse_lazy('dashboard')

     # check if user actually created the hall....
    def get_object(self):
        hall = super(UpdateHall, self).get_object()
        if not hall.user == self.request.user:
            raise Http404
        return hall

class DeleteHall(LoginRequiredMixin, generic.DeleteView):
    model = Hall
    template_name = 'halls/delete_hall.html'
    success_url = reverse_lazy('dashboard')

     # check if user actually created the hall....
    def get_object(self):
        hall = super(DeleteHall, self).get_object()
        if not hall.user == self.request.user:
            raise Http404
        return hall


