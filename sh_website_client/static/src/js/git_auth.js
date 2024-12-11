import { _t } from "@web/core/l10n/translation";
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.login_github = publicWidget.Widget.extend({
    selector: '.oe_login_form',
    events: {
        'click #signup-git': 'signup_git',
        'click .field-platform .btn': 'sign_platform',        
        'blur input[name=password]': 'validate_password',
        'blur input[name=username]': 'validate_username',
    },
    init() {
        if($(".oe_login_form").length > 0)
        {
            $(".field-access_token").hide();
            $("button[type='submit']").hide();
            $("#signup-git").fadeIn();
        }
        if($(".oe_signup_form").length > 0)
        {
            $(".field-access_token").fadeIn();
            $("button[type='submit']").hide();
            $("#signup-git").fadeIn();
        }   
    },
    validate_password : function(event){
        $("input[name=confirm_password]").val($("input[name=password]").val());
        $("input[name=_gpassword]").val($("input[name=password]").val());
        $("input[name=_gpassword]").val($("input[name=password]").val());
    },
    validate_username : function(event){
        var username = $(event.currentTarget).val();
        $(event.currentTarget).val(String(username).toLowerCase());
    },
    sign_platform : function (event) {        
        event.preventDefault();   
        $(".field-platform .btn").removeClass("btn-selected");
        var _button = $(event.currentTarget);
        _button.addClass("btn-selected");
        _button.fadeIn("slow");
        var platform = $(".btn-selected").attr("platform");

        if(platform=="odoo")
        {
            $(".field-username").css("display","none").val('');
            $(".field-login").fadeIn("slow").val('').focus();           
        }
        else
        {
            $(".field-login").css("display","none").val('');
            $(".field-username").fadeIn("slow").val('').focus();
        }
    },
    
    auth_connect: function(params)
    {
        var dialog = this.bindService("notification"); 
        var data = { "params": params }
        
        $.ajax({
            type: "POST",
            url: '/git/auth_connect',
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: "application/json",
            async: false,
            success: function (response) {
                var git_response = response.result;
                
                try
                {
                    if(git_response['status'] == 'error')
                    {
                        dialog.add(git_response['message'],{'title':String(params['platform']).toUpperCase() +  _t(' SIGN IN'),sticky: true,'type':'warning'});
                    }
                }
                catch(exception)
                {

                }  

                if(String(params['platform']) == "odoo")
                {
                    $(".oe_login_buttons button[type='submit']").click();
                }
                else
                {
                    $("input[name=identifier]").val(git_response['id']);
                    $("input[name=login]").val(git_response['username']);
                    $("input[name=name]").val(git_response['full_name']);
                    $("input[name=html_url]").val(git_response['html_url']);
                    if(String(git_response['id']).length > 0)
                    {
                        $(".oe_login_buttons button[type='submit']").click();
                    }
                }                
            }
        });
    },
    signup_git : function(event)
    {
        
       event.preventDefault();        
       
        var platform = $(".btn-selected").attr("platform");
        var username = $("input[name=username]").val();
        var password = $("input[name=password]").val();        
        var access_token = $("input[name=access_token]").val(); 
        
        $("input[name=platform]").val(platform);      

        if(platform=="odoo")
        {        
            try
            {
                $("input[name=username]").val("***"); 
                $(".oe_login_buttons button[type='submit']").click();
            }
            catch(error)
            {

            }                  
        }
        else
        {
            
           var dialog = this.bindService("notification");     
            
            if ($("input[name=access_token]").length > 0)
            {
                if(!access_token)
                {
                    dialog.add(_t("Type Access Token."),{'title':String(platform).toUpperCase() +  _t(' SIGN IN'),sticky: true,'type':'warning'});
                }
            }
            

            if(!username || !password)
            {
                $(".oe_login_buttons button[type='submit']").click();
                dialog.add(_t("Username or Password is not valid."),{'title':String(platform).toUpperCase() +  _t(' SIGN IN'),sticky: true,'type':'warning'});
            }            
            else
            {                
                var params = {'platform':platform, 'username':username, 'password':password, 'access_token':access_token};                
                this.auth_connect(params);  
            }
        }
    },
});

publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
    selector: '.oe_signup_form',
    events: {
        'click #signup-git': 'signup_git',
    },
    signup_git : function(event)
    {

        event.preventDefault();        

        var platform = $(".btn-selected").attr("platform");
        var username = $("input[name=username]").val();
        var password = $("input[name=password]").val();        
        var access_token = $("input[name=access_token]").val(); 

        $("input[name=platform]").val(platform);      

        if(platform=="odoo")
        {        
            $("input[name=username]").val("***"); 
            $(".oe_login_buttons button[type='submit']").click();     
        }
        else
        {
            var dialog = this.bindService("notification");     
            
            if ($("input[name=access_token]").length > 0)
            {
                if(!access_token)
                {
                    dialog.add(_t("Type Access Token."),{'title':String(platform).toUpperCase() +  _t(' SIGN IN'),sticky: true,'type':'warning'});
                }
            }
            

            if(!username || !password)
            {
                $(".oe_login_buttons button[type='submit']").click();
                dialog.add(_t("Username or Password is not valid."),{'title':String(platform).toUpperCase() +  _t(' SIGN IN'),sticky: true,'type':'warning'});
            }            
            else
            {                
                var params = {'platform':platform, 'username':username, 'password':password, 'access_token':access_token};
                this.auth_connect(params);  
            }
        }
    },
    auth_connect: function(params)
    {
        var dialog = this.bindService("notification"); 
        var data = { "params": params }
        $.ajax({
            type: "POST",
            url: '/git/auth_connect',
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: "application/json",
            async: false,
            success: function (response) {
                var git_response = response.result;

                try
                {
                    if(git_response['status'] == 'error')
                    {
                        dialog.add(git_response['message'],{'title':String(params['platform']).toUpperCase() +  _t(' SIGN IN'),sticky: true,'type':'warning'});
                    }
                }
                catch(exception)
                {

                }  

                if(String(params['platform']) == "odoo")
                {
                    $(".oe_login_buttons button[type='submit']").click();
                }
                else
                {
                    $("input[name=identifier]").val(git_response['id']);
                    $("input[name=login]").val(git_response['username']);
                    $("input[name=name]").val(git_response['full_name']);
                    $("input[name=html_url]").val(git_response['html_url']);
                    $("input[name=confirm_password]").val(git_response['password']);
                    if(String(git_response['id']).length > 0)
                    {
                       $(".oe_login_buttons button[type='submit']").click();
                    }
                }                
            }
        });
    } 
});