from rest_framework.views import APIView, status, Request
from rest_framework.response import Response
from pets.models import Pet
from pets.serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination
from groups.models import Group
from traits.models import Trait


class PetView(APIView, PageNumberPagination):           
    def post(self, request: Request):
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group_get = serializer.validated_data.pop("group")
        trait_get = serializer.validated_data.pop("traits")

        group_filtered, created = Group.objects.get_or_create(scientific_name__iexact=group_get["scientific_name"], defaults=group_get)
        pet_add = Pet.objects.create(group=group_filtered, **serializer.validated_data)

        trait_filtered = [Trait.objects.get_or_create(name__iexact=trait["name"], defaults=trait)[0] for trait in trait_get]
        pet_add.traits.add(*trait_filtered)

        serializer = PetSerializer(pet_add)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request: Request):
        trait = request.query_params.get("trait")
        
        if trait:     
            pets = Pet.objects.filter(
                traits__name=trait
            )
            result_page = self.paginate_queryset(pets, request, view=self)
            serializer = PetSerializer(result_page, many=True)
            return self.get_paginated_response(serializer.data)

        pets = Pet.objects.all()
        result_page = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)


class PetViewId(APIView):
    def get(self, request: Request, pet_id):
        try:
            pet = Pet.objects.get(pk=pet_id)
            serializer = PetSerializer(pet, many=False)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found"}, 404)
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id):
        try:
            pet = Pet.objects.get(pk=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found"}, 404)
        pet.delete()
        return Response(None, status.HTTP_204_NO_CONTENT) 
    
    def patch(self, request: Request, pet_id):
        try:
            pet = Pet.objects.get(pk=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found"}, 404) 

        serializer = PetSerializer(pet, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        pet.name = serializer.validated_data.get('name', pet.name)
        pet.age = serializer.validated_data.get('age', pet.age)

        group_get = serializer.validated_data.get('group')
        if group_get:
            group_filtered, created = Group.objects.get_or_create(scientific_name__iexact=group_get["scientific_name"], defaults=group_get)
            pet.group = group_filtered

        trait_get = serializer.validated_data.get('traits')
        if trait_get:
            trait_filtered = [Trait.objects.get_or_create(name__iexact=trait["name"], defaults=trait)[0] for trait in trait_get]
            pet.traits.set(trait_filtered)

        pet.save()

        serializer = PetSerializer(pet)
        return Response(serializer.data, status=status.HTTP_200_OK)