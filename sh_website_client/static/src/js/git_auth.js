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
        var $buttons = $(".field-platform .btn");
        var $selectedButton = $(event.currentTarget);

        // Update button selection state
        $buttons.removeClass("btn-selected");
        $selectedButton.addClass("btn-selected");

        var platform = $selectedButton.attr("platform");

        // Get jQuery objects for the relevant form fields
        var $usernameFieldDiv = $(".form-group.field-username");
        var $usernameInput = $usernameFieldDiv.find("input#username");
        var $tokenLinkDiv = $(".form-group.field-token");
        var $tokenLink = $tokenLinkDiv.find("a");
        var $accessTokenDiv = $(".form-group.field-access_token");
        var $accessTokenLabel = $accessTokenDiv.find("label[for='access_token']");
        var $accessTokenInput = $accessTokenDiv.find("input#access_token"); // Added for clarity if needed later

        var $odooLoginDiv = $(".field-login"); // Odoo's standard login field (e.g., email)
        var $platformHiddenInput = $("input[name='platform']");

        // Default state: hide platform-specific fields
        $usernameFieldDiv.hide();
        $tokenLinkDiv.hide();
        $accessTokenDiv.hide();
        $odooLoginDiv.hide(); // Hide Odoo login field by default

        if (platform === "odoo") {
            // Show Odoo login field
            $odooLoginDiv.fadeIn("slow");
            $odooLoginDiv.find("input").val('').focus(); // Clear and focus Odoo login input
            $platformHiddenInput.val('odoo'); // Set platform value if needed for Odoo
        } else {
            // Show platform-specific fields (GitHub or Bitbucket)
            $usernameFieldDiv.fadeIn("slow");
            $usernameInput.val('').focus(); // Clear and focus username input
            $tokenLinkDiv.fadeIn("slow");
            $accessTokenDiv.fadeIn("slow");
            $accessTokenInput.val(''); // Clear any previous token
            $platformHiddenInput.val(platform); // Set to 'github' or 'bitbucket'

            if (platform === "github") {
                $usernameInput.attr("placeholder", "GitHub Username");
                $tokenLink.attr("href", "https://github.com/settings/tokens").text("Obtener Token en GitHub");
                $accessTokenLabel.text("Access Token");
            } else if (platform === "bitbucket") {
                $usernameInput.attr("placeholder", "Bitbucket Username");
                $tokenLink.attr("href", "https://bitbucket.org/account/settings/app-passwords/").text("Obtener App Password en Bitbucket");
                $accessTokenLabel.text("App Password"); // Bitbucket calls them App Passwords
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
        var $form = $(event.currentTarget).closest('form');

        // Always set the hidden platform input
        $form.find("input[name='platform']").val(platform);

        if (platform === "bitbucket") {
            // OAuth Flow for Bitbucket
            var odoo_login = $form.find("input[name='login']").val();
            var odoo_name = $form.find("input[name='name']").val();
            var odoo_password = $form.find("input[name='password']").val();
            var odoo_confirm_password = $form.find("input[name='confirm_password']").val();
            var dialog = this.bindService("notification");

            // Client-side validation for Odoo fields
            if (!odoo_login) {
                dialog.add(_t("Email is required."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            if (!odoo_name) {
                dialog.add(_t("Name is required."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            if (!odoo_password || !odoo_confirm_password) {
                dialog.add(_t("Password and confirmation are required."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            if (odoo_password !== odoo_confirm_password) {
                dialog.add(_t("Passwords do not match."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            // If Odoo fields are valid, change action and submit to Bitbucket OAuth initiation controller
            $form.attr('action', '/bitbucket/signup/initiate');
            $form.submit();
        }
        else if (platform === "odoo") {
            // Standard Odoo signup
            $form.find("input[name=username]").val("***"); // Compatibility with previous logic
            // Ensure the form submits to the standard Odoo signup action if different
            // or let Odoo's default form submission handle it by not interfering further.
            // This click might need to target a more specific Odoo submit button if one exists.
            $(".oe_login_buttons button[type='submit']").click();     
        }
        else // For GitHub (and any other non-Odoo, non-Bitbucket OAuth platforms)
        {
            // This block now handles GitHub (username/token) and potentially other similar flows
            var username = $form.find("input[name=username]").val();
            var password = $form.find("input[name=password]").val(); // Odoo password
            var access_token = $form.find("input[name=access_token]").val(); // GitHub token
            var dialog = this.bindService("notification");

            if (platform === "github") {
                if (!username) {
                    dialog.add(_t("GitHub Username is required."), {
                        title: 'GITHUB SIGN UP', 
                        sticky: false, 
                        type: 'warning'
                    });
                    return;
                }
                if ($form.find("input[name=access_token]").length > 0 && !access_token) {
                    dialog.add(_t("Please provide your Access Token."), {
                        title: 'GITHUB SIGN UP', 
                        sticky: false, 
                        type: 'warning'
                    });
                    return;
                }
            } 
            // Add similar blocks here if you have other platforms using username/token
            
            // Common Odoo Password Validation (required for creating the Odoo user)
            if (!password) {
                dialog.add(_t("Password is required."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            
            var params = {'platform': platform, 'username': username, 'password': password, 'access_token': access_token};
            this.auth_connect(params); // Calls your existing AJAX flow for GitHub
        }
    },
});

publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
    selector: '.oe_signup_form',
    events: {
        'click #signup-git': 'signup_git',
        'click .field-platform .btn': 'sign_platform',
    },
    sign_platform : function (event) {
        event.preventDefault();
        var $buttons = $(".field-platform .btn");
        var $selectedButton = $(event.currentTarget);

        // Update button selection state
        $buttons.removeClass("btn-selected");
        $selectedButton.addClass("btn-selected");

        var platform = $selectedButton.attr("platform");

        var $usernameFieldDiv = $(".form-group.field-username");
        var $usernameInput = $usernameFieldDiv.find("input#username");
        var $tokenLinkDiv = $(".form-group.field-token");
        var $tokenLink = $tokenLinkDiv.find("a");
        var $accessTokenDiv = $(".form-group.field-access_token");
        var $accessTokenLabel = $accessTokenDiv.find("label[for='access_token']");
        var $accessTokenInput = $accessTokenDiv.find("input#access_token");
        var $odooLoginDiv = $(".field-login");
        var $platformHiddenInput = $("input[name='platform']");

        // Default behavior: Hide all platform-specific conditional fields
        $usernameFieldDiv.hide();
        $tokenLinkDiv.hide();
        $accessTokenDiv.hide();
        $odooLoginDiv.hide();

        $platformHiddenInput.val(platform);

        if (platform === "odoo") {
            $odooLoginDiv.fadeIn("slow");
            $odooLoginDiv.find("input").val('').focus();
        } else if (platform === "github") {
            $usernameFieldDiv.fadeIn("slow");
            $usernameInput.val('').attr("placeholder", "GitHub Username").focus();
            $tokenLinkDiv.fadeIn("slow");
            $tokenLink.attr("href", "https://github.com/settings/tokens").text("Obtener Token en GitHub");
            $accessTokenDiv.fadeIn("slow");
            $accessTokenLabel.text("Access Token");
            $accessTokenInput.val('');
        } else if (platform === "bitbucket") {
            // For Bitbucket OAuth flow, username & app password fields from the form are NOT used.
            // They remain hidden. User will be redirected to Bitbucket to authorize.
            // The standard Odoo signup fields (name, email, password) will be used.
            // Optionally, focus on the main Odoo password field if needed.
            if ($(".oe_signup_form input[name='password']").length > 0 && $(".oe_signup_form input[name='password']").val() === '') {
                 // $(".oe_signup_form input[name='password']").focus(); 
            }
        }
    },
    signup_git : function(event)
    {
        event.preventDefault();
        var platform = $(".btn-selected").attr("platform");
        var $form = $(event.currentTarget).closest('form');

        // Always set the hidden platform input
        $form.find("input[name='platform']").val(platform);

        if (platform === "bitbucket") {
            // OAuth Flow for Bitbucket
            var odoo_login = $form.find("input[name='login']").val();
            var odoo_name = $form.find("input[name='name']").val();
            var odoo_password = $form.find("input[name='password']").val();
            var odoo_confirm_password = $form.find("input[name='confirm_password']").val();
            var dialog = this.bindService("notification");

            if (!odoo_password || !odoo_confirm_password) {
                dialog.add(_t("Password and confirmation are required."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            if (odoo_password !== odoo_confirm_password) {
                dialog.add(_t("Passwords do not match."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            // If Odoo fields are valid, change action and submit to Bitbucket OAuth initiation controller
            $form.attr('action', '/bitbucket/signup/initiate');
            $form.submit();
        }
        else if (platform === "odoo") {
            // Standard Odoo signup
            $form.find("input[name=username]").val("***"); // Compatibility with previous logic
            // Ensure the form submits to the standard Odoo signup action if different
            // or let Odoo's default form submission handle it by not interfering further.
            // This click might need to target a more specific Odoo submit button if one exists.
            $(".oe_login_buttons button[type='submit']").click();     
        }
        else // For GitHub (and any other non-Odoo, non-Bitbucket OAuth platforms)
        {
            // This block now handles GitHub (username/token) and potentially other similar flows
            var username = $form.find("input[name=username]").val();
            var password = $form.find("input[name=password]").val(); // Odoo password
            var access_token = $form.find("input[name=access_token]").val(); // GitHub token
            var dialog = this.bindService("notification");

            if (platform === "github") {
                if (!username) {
                    dialog.add(_t("GitHub Username is required."), {
                        title: 'GITHUB SIGN UP', 
                        sticky: false, 
                        type: 'warning'
                    });
                    return;
                }
                if ($form.find("input[name=access_token]").length > 0 && !access_token) {
                    dialog.add(_t("Please provide your Access Token."), {
                        title: 'GITHUB SIGN UP', 
                        sticky: false, 
                        type: 'warning'
                    });
                    return;
                }
            } 
            // Add similar blocks here if you have other platforms using username/token
            
            // Common Odoo Password Validation (required for creating the Odoo user)
            if (!password) {
                dialog.add(_t("Password is required."), {'title': _t('SIGN UP'), sticky: false, 'type': 'warning'});
                return;
            }
            
            var params = {'platform': platform, 'username': username, 'password': password, 'access_token': access_token};
            this.auth_connect(params); // Calls your existing AJAX flow for GitHub
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