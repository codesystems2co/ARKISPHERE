import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { markup } from "@odoo/owl";

publicWidget.registry.sh_git_stages = publicWidget.Widget.extend({
    'selector': '.my-stages-page',
    events: {
        'click #sh-new-repository': 'sh_new_repository',
        'click #sh-save-repository': 'create_git_repository',
        'click #sh-cancel-repository': 'sh_cancel_repository',
        'click a.sh-app-logs-tab': 'sh_app_logs_tab',
        'click a#app-dashboard': 'app_dashboard',
        'click .sh-tab-stages .nav-link': 'sh_tab_stages',
        'change select#deployments_options': 'deployments_options',
        'click a.row-branch-item': 'load_branch_panel',
        'click #assign_collaborator': 'handle_assign_collaborator',
        'click #save_command': 'handle_save_command',
        'click #assign_domain': 'handle_assign_domain',
        'click a.sh-shell-tab': 'handle_sh_shell_tab',
        'click #create_branch_from': 'create_branch_from',
        'click a#restart-branch': 'handle_restart_branch',
        'click #ssl_create_self_signed': 'handle_ssl_create_self_signed',
        'click #ssl_create': 'handle_ssl_create',
        'change select#_ssl_type': 'handle_ssl_type',
        'click i.delete_domain': 'handle_delete_domain',
        'click i.unssign_collaborator': 'handle_unssign_collaborator',
        'click i.delete_branch': 'delete_branch',
        'change select#restore_way': 'handle_restore_way',
        'change select#github_repositories': 'handle_github_repositories',
        'click a.manual-backup': 'manual_backup',
        'click a.download-row-button': 'download_from_local',
        'click a.restore-row-button': 'restore_from_local',
        'change select#github_repositories': 'handle_repository_branches_tree',
    },
    init() {
        this._super(...arguments);        

        if ($("a.row-branch-item").length > 0) {
            this.autor_and_collaborators_control();
        }

        if ($("select#sh_repository_visibility").length > 0) {
            this.get_deployments_all();
        }

        if ($("a.row-branch-item").length > 0) {
            this.get_git_project_branch_commits($("a.row-branch-item").first());
            this.get_code_editor($("a.row-branch-item").first());
            this.get_pgadmin($("a.row-branch-item").first());
            this.get_branch_connect($("a.row-branch-item").first());
            this.get_collaborators($("a.row-branch-item").first());
            this.get_domains($("a.row-branch-item").first());
            this.get_domains_ssl($("a.row-branch-item").first());
            this.get_commands($("a.row-branch-item").first());
            this.get_branches($("a.row-branch-item").first());
            this.get_backups($("a.row-branch-item").first());
        }

        $(".sh-form-new-repository").find(".row-spinner").fadeOut();
    },
    base64_to_blob:function(base64String, contentType = '') {
        const byteCharacters = atob(base64String);
        const byteArrays = [];
    
        for (let i = 0; i < byteCharacters.length; i++) {
            byteArrays.push(byteCharacters.charCodeAt(i));
        }
    
        const byteArray = new Uint8Array(byteArrays);
        return new Blob([byteArray], { type: contentType });
    },
    save_blob_as_text_file: function(blob, fileName) {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        link.click();
    },
    download_from_local: function(event)
    {
        var self = this;
        var revision = $(event.currentTarget).attr('revision');
        var notification = self.bindService("notification"); 
        var orm = self.bindService("orm");
        try {
            var orm = this.bindService("orm");
            $('#sh-backups-tab .sh-backups-table').hide();
            $('#sh-backups-tab .row-spinner').fadeIn(); 
            orm.call('sh.backup', 'download_from_local', ["", revision])
                .then(
                    function (response) {
                        if (String(response.error) == 'true')
                        {
                            notification.add(response.message, { 'title': _t('Download Backup Revision'), sticky: false })
                            $("html, body").animate({ scrollTop: 0 }, "fast");
                        }
                        else
                        {
                            if(response.google_drive_share_file_link)
                            {
                                const link = document.createElement('a');
                                link.target = '_blank'
                                link.href = response.google_drive_share_file_link;
                                link.click();
                                return
                            }
                            else
                            {
                                var content_type = 'application/zip';
                                var blob = self.base64_to_blob(response.base, content_type);
                                self.save_blob_as_text_file(blob, response.filename);
                            }                            
                        }  
                        $('#sh-backups-tab .row-spinner').hide();
                        $('#sh-backups-tab .sh-backups-table').slideDown();                      
                    });
        }
        catch(error)
        {console.log(error)}
    },
    restore_from_local: function(event)
    {
        var self = this;
        var revision = $(event.currentTarget).attr('revision');
        var btn = $(".row-active");
        var branch_id = btn.attr("branch_id");
        var notification = self.bindService("notification"); 
        var orm = self.bindService("orm");
        try {
            var orm = this.bindService("orm");
            $('#sh-backups-tab .sh-backups-table').hide();
            $('#sh-backups-tab .row-spinner').fadeIn();  
            orm.call('sh.backup', 'restore_from_local', ["", branch_id, revision])
                .then(
                    function (response) {
                        if (String(response.error) == 'true')
                        {
                            notification.add(response.message, { 'title': _t('Restore Backup Revision'), sticky: false })                            
                        }
                        else
                        {
                            notification.add(_t('Revision was restored succesful.'), { 'title': _t('Restore Backup Revision'), sticky: false , 'type':'success'})                            
                        } 
                        $("html, body").animate({ scrollTop: 0 }, "fast");  
                        $('#sh-backups-tab .row-spinner').hide();
                        $('#sh-backups-tab .sh-backups-table').slideDown();                     
                    });
        }
        catch(error)
        {console.log(error)}
    },
    manual_backup: function(event)
    {
        var self = this;
        var btn = $(".row-active");
        var branch_id = btn.attr("branch_id");
        var orm = self.bindService("orm");
        try {
            var branch_id = btn.attr("branch_id");
            var orm = this.bindService("orm");
            $('#sh-backups-tab .sh-backups-table').hide();
            $('#sh-backups-tab .row-spinner').fadeIn();            
            orm.call('sh.backup', 'manual_backup_database', ["", branch_id])
                .then(
                    function (response) {
                        self.get_backups(btn);
                        $('#sh-backups-tab .row-spinner').hide();
                        $('#sh-backups-tab .sh-backups-table').slideDown();
                    });
        }
        catch(error)
        {console.log(error)}
    },
    get_backups:function(btn)
    {
        console.log('get_backups revisions >>');
        var self = this;
        var dialog = self.bindService("notification");        
        var orm = self.bindService("orm");
        try {
            var branch_id = btn.attr("branch_id");
            var orm = this.bindService("orm");
            var table = String()
            orm.call('sh.backup.revision', 'get_branch_backup_revisions', ["", branch_id])
                .then(
                    function (revisions) {
                        if(revisions.length > 0)
                        {
                            for(var i=0;i<revisions.length;i++)
                            {
                                var revision = revisions[i];
                                table += '<tr>';
                                    table += '<td>' + String(revision['name']) + '</td>'; 
                                    table += '<td>' + String(revision['branch'][1]) + '</td>';
                                    table += '<td>' + String(revision['version']) + '</td>';
                                    table += '<td>' + String(revision['type']) + '</td>';
                                    table += '<td><div class="revision-container"><a href="#">' + String(revision['revision']).substring(0,15) + '...</a></div></td>';
                                    table += '<td>';                                
                                        table += '<div class="table-panel-buttons">';
                                            table += '<a class="btn btn-primary download-row-button" title="Download" revision="' + String(revision['revision']) + '" ><i class="fa fa-download"></i></a>';
                                            table += '<a class="btn btn-secondary restore-row-button" title="Restore" revision="' + String(revision['revision']) + '" ><i class="fa fa-upload"></i></a>';
                                        table += '</div>';
                                    table += '</td>';
                                table += '</tr>';
                            }
                            $(".tbody-revisions").html(table);
                        }
                        else
                        {
                            table += '<tr>';
                                table += '<td>' + _t("0 Records") + '</td>'; 
                            table += '</tr>';
                            $(".tbody-revisions").html(table);
                        }
                    });
        }
        catch(error)
        {console.log(error)}
    },
    create_git_repository: function (event) {
        var self = this;
        var restore_way = $("#restore_way").val();
        var repository_name = $("#sh_repository_name").val();
        var main_branch = {'name':$("#github_repository_branches").val(),'sha':$("#github_repository_branches").attr('sha')}
        var database64 = null;
        var repository_visibility = $("#sh_repository_visibility").val();
        var kuber_deployment = $("#deployments_options").val();
        var server_id = $("#sh_so_server").text().trim();
        var notification = this.bindService("notification");

        if (restore_way=='odoo_sh')
        {
            repository_name = $("#github_repositories").val();
            var reader = new FileReader();
            if(document.querySelector('input#database').files[0] == undefined || document.querySelector('input#database').files[0] == null)
            {
                notification.add(_t("Kindly, browse a valid .zip file type"), { 'title': _t('Restore Project'), sticky: false })
                $('input#database').val('')
            }
            try 
            {
                var file_types = ['zip'];
                    var extension = document.querySelector('input#database').files[0].name.split('.').pop().toLowerCase(),
                    is_success = file_types.indexOf(extension) > -1;
                    if(is_success)
                    {
                        var database = document.querySelector('input#database').files[0];
                        reader.readAsDataURL(database);
                        reader.onload = function ()
                        {                            
                            database64 = reader.result;                    
                            var params = { 'restore_way': restore_way,'_name': repository_name, '_visibility': repository_visibility, '_server_id': server_id, '_kuber_deployment': kuber_deployment, 'main_branch':main_branch, 'database64':database64 }
                            self._create_git_repository(params);   
                            self.handle_create_git_repository_form();
                        }
                    }
                    else
                    {
                        notification.add(_t("Kindly, browse a valid .zip file type"), { 'title': _t('Restore Project'), sticky: false })
                        $('input#database').val('');
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }                
            }
            catch (error) 
            {
                notification.add(_t("Kindly, browse a valid .zip file type"), { 'title': _t('Restore Project'), sticky: false })
                $("html, body").animate({ scrollTop: 0 }, "fast");
            }
        }
        else
        {
            var params = { 'restore_way': restore_way,'_name': repository_name, '_visibility': repository_visibility, '_server_id': server_id, '_kuber_deployment': kuber_deployment, 'main_branch':main_branch}
            self.handle_create_git_repository_form();
            self._create_git_repository(params);            
        }        
    },
    handle_repository_branches_tree: function(event)
    {
        var repository_name = $('select#github_repositories').val();
        $('select#github_repository_branches option').hide();
        var options = $('select#github_repository_branches option[repository="'+String(repository_name)+'"]');
        if( options.length > 0 )
        {
            options.first().prop('selected', true).attr('selected', 'selected')
            options.each(function() {
                if($(this).val()=='main')
                    {
                        $(this).prop('selected', true).attr('selected', 'selected');
                    }
                $(this).show();
              });
            
                /*if($(this).val()=='main')
                {
                    $(this).prop('selected', true).attr('selected', 'selected');
                }
                $(this).show();*/
        }        
    },
    handle_create_git_repository_form:function()
    {
        $(".sh-form-new-repository").find(".row-spinner").fadeIn();
        $(".sh-form-new-repository").find("input").attr('disabled', 'disabled');
        $(".sh-form-new-repository").find("select").attr('disabled', 'disabled');
        $(".sh-form-new-repository").find(".btn").attr('disabled', 'disabled');
        $("#sh-save-repository").remove();  
    },
    _create_git_repository:function(params)
    {
        var self = this;
        var dialog = self.bindService("notification");        
        try {

            var orm = this.bindService("orm");
            orm.call('sh.git_repository', 'create_git_repository', ["", params])
                .then(
                    function (response) {
                        console.log(response)
                        self.hide_new_repository_form();
                        var button_reload = [
                            {
                                name: _t("OK"),
                                primary: true,
                                onClick: () => {
                                    location.reload();
                                },
                            },
                            {
                                name: _t("Update Token"),
                                primary: true,
                                onClick: () => {
                                    window.open(
                                        "//github.com/settings/tokens/",
                                        '_blank'
                                    );
                                },
                            },
                        ];

                        var button_reload_success = [
                            {
                                name: _t("OK"),
                                primary: true,
                                onClick: () => {
                                    location.reload();
                                },
                            },
                        ];

                        if (String(response.error) == 'true') {
                            dialog.add(response.message, { 'title': _t('NEW PROJECT'), sticky: false, buttons: button_reload });
                            $("html, body").animate({ scrollTop: 0 }, "fast");
                        }
                        else {
                            dialog.add(response.message, { 'title': _t('NEW PROJECT'), sticky: false, 'type': 'success', buttons: button_reload_success });
                            $("html, body").animate({ scrollTop: 0 }, "fast");
                            setInterval(function () { location.reload(); }, 6000);
                        }

                        $(".sh-form-new-repository").find(".row-spinner").fadeOut();
                    }
                )
        } catch (e) {
            setInterval(function () { location.reload(); }, 300000);
        }
    },
    handle_restore_way: function(event)
    {
        var restore_way = $(event.currentTarget).val();
        if(restore_way == "standar")
        {
            $(".from-repository").hide();
            $(".from-scratch").fadeIn();
        }
        if(restore_way == "odoo_sh")
        {
            $(".from-scratch").slideUp();
            this.get_github_project();
        }
    },
    handle_github_repositories: function(event)
    {
        var restore_way = $(event.currentTarget).val();
    },
    handle_delete_domain: function (event) {
        this.delete_domain($(event.currentTarget))
    },
    handle_unssign_collaborator: function (event) {
        this.unssign_collaborator($(event.currentTarget))
    },
    create_branch_from: function (event) {
        event.preventDefault();
        var self = this;
        var dialog = this.bindService("dialog");
        var notification = this.bindService("notification");

        var new_referenced_branch = $("input#new-referenced-branch").val();
        if (String(new_referenced_branch).length <= 0) {
            notification.add(_t("Kindly, type stage name"), { 'title': _t('New Stage'), sticky: false })
            return
        }

        dialog.add(ConfirmationDialog, {
            body: _t("Confirm and create a new branch from ") + String($('select#from-branches').text()),
            confirm: () => {
                $(".new-branch-spinner").fadeIn();
                $("#new-referenced-branch").fadeOut();
                $("#create_branch_from").fadeOut();
                self.create_git_repository_branch_from();
            },
            cancel: () => { $("#new-referenced-branch").val(""); },
            title: _t('New Stage'),
        });
        $("html, body").animate({ scrollTop: 0 }, "fast");
    },
    handle_ssl_type: function (event) {
        event.preventDefault();
        var ssl_type = $(event.currentTarget).val();
        if (ssl_type == 'self') {
            $('div.ssl-file').fadeOut();
            $('#ssl_create_self_signed').fadeIn();
        }
        else {
            $('div.ssl-file').fadeIn();
            $('#ssl_create_self_signed').fadeOut();
        }
    },
    handle_ssl_create: function (event) {
        event.preventDefault();
        this.create_ssl($(".row-active"), "external");
    },
    handle_ssl_create_self_signed: function (event) {
        event.preventDefault();
        this.create_ssl($(".row-active"), "internal");
    },
    handle_restart_branch: function (event) {
        event.preventDefault();
        this.restart_branch($(".row-active"));
    },
    handle_assign_collaborator: function (event) {
        event.preventDefault();
        this.assign_collaborator($(".row-active"));
    },
    handle_save_command: function (event) {
        event.preventDefault();
        this.save_command($(".row-active"));
        this.web_execute_command($(event.currentTarget));
    },
    load_branch_panel: function (event) {
        event.preventDefault();
        $("a.row-branch-item").removeClass("row-active");
        this.get_git_project_branch_commits($(event.currentTarget))
        this.get_branch_connect($(event.currentTarget));
        this.get_collaborators($(event.currentTarget));
        this.get_domains($(event.currentTarget));
        this.get_domains_ssl($(event.currentTarget));
        this.get_commands($(event.currentTarget));
        this.get_branches($(event.currentTarget));
        $(event.currentTarget).addClass("row-active");
    },
    handle_assign_domain: function (event) {
        event.preventDefault();
        this.assign_domain($(".row-active"));
    },
    handle_sh_shell_tab: function (event) {
        event.preventDefault();
        window.open(
            $(event.currentTarget).attr('external_editor'),
            '_blank'
        );
    },
    delete_branch: function(event)
    {
        event.preventDefault();
        var orm = this.bindService("orm");
        var dialog = this.bindService("dialog");
        var notification = this.bindService("notification");
        var branch_id = $("select#github_branches").val();
        
        if(branch_id=='Select')
        {
            notification.add(_t('Select a branch'),{'title':_t('Stages'),'sticky':false}); 
            return
        }

        dialog.add(ConfirmationDialog, {
            body: markup("<input name='_github_password' placeholder='Gihub Password' class='form-control'/>"),
            confirm: () => {
                var _github_password = $("input#_github_password").val();
                orm.call('git.autor', 'check_github_password', ["", _github_password])
                .then(
                    function (state) {
                        console.log(String(state) )
                        if (String(state) == String('true'))
                        {
                            console.log(String('777') )
                            orm.call('sh.git_branch', 'delete_branch', ["", branch_id])
                            .then(
                                function (response) {
                                    if( String(response.state) == String('ok'))
                                    {
                                        notification.add(response.message,{'title':_t('Stages'),'sticky':false,'type':success}); 
                                    }
                                    else
                                    {
                                        notification.add(response.message,{'title':_t('Stages'),'sticky':false}); 
                                    }
                                }
                            );
                        }
                        else
                        {
                            console.log(String('999') )
                            notification.add(_t('Password did not match with your account'),{'title':_t('Stages'),'sticky':false}); 
                        }
                    }
                );

                
            },
            cancel: () => { $("select#github_branches").val("Select"); },
            title: _t('New Stage'),
        });     
        $("html, body").animate({ scrollTop: 0 }, "fast");    
    },
    deployments_options: function (event) {
        event.preventDefault();
        var so_server = $('option:selected', $(event.currentTarget)).attr('so_server');
        $(".deploy_so_server").html(so_server);
    },
    get_github_project: function () {
        var self = this
        var orm = this.bindService("orm");
        orm.call('sh.git_repository', 'get_github_project', [""])
            .then(
                    function (_response) 
                    {
                        var repository_options = String()
                        var branch_options = String()
                        if(String(_response.error) == String('true'))
                        {}
                        else
                        {
                            for(var i=0; i<_response['data'].length; i++)
                            {
                                var repository = _response.data[i][0]['repository'];
                                var branches = _response.data[i][1]['branches'];
                                
                                repository_options += String("<option value="+String(repository.name)+">");
                                repository_options += String(repository.name);
                                repository_options += String("</option>");

                                for(var j=0; j<branches.length; j++)
                                {
                                    var branch = branches[j];
                                    branch_options += String("<option value="+String(branch.name)+" value="+String(branch.sha)+" repository="+String(repository.name)+">");
                                    branch_options += String(branch.name);
                                    branch_options += String("</option>");
                                }
                            }
                        }
                        $('select#github_repositories').html(repository_options);
                        $('select#github_repository_branches').html(branch_options);
                        $(".from-repository").fadeIn();  
                        self.handle_repository_branches_tree(null)
                    }
                 )
    },
    sh_tab_stages: function (event) {
        event.preventDefault();
        $(".sh-tab-stages .nav-link").removeClass("active");
        $(".sh-tab-stages .tab-pane").removeClass("active");
        $(event.currentTarget).addClass("active");
        var tab_content_id = $(event.currentTarget).attr("href");
        $(tab_content_id).addClass("active");
    },
    sh_cancel_repository: function (event) {
        event.preventDefault();
        this.hide_new_repository_form();
    },
    sh_new_repository: function (event) {
        event.preventDefault();
        var dialog = this.bindService("notification");
        var has_deployment = ($("select#deployments_options option").length > 0) ? true : false;
        if (!has_deployment) {
            dialog.add(_t('It seems you have not deployments available'), { 'title': _t('New Deployment'), sticky: false })
            $("html, body").animate({ scrollTop: 0 }, "fast");
            return
        }
        $("#sh-new-repository").hide();
        $(".sh-form-new-repository").slideDown("fast");
        $(".sh-form-new-repository").fadeIn("slow");
        $("#sh-cancel-repository").fadeIn("slow");
    },
    sh_app_logs_tab: function (event) {
        event.preventDefault()
        var branch_id = $("div.branches-columned a.row-active").attr("branch_id");
        var data = { "params": { "branch_id": branch_id } }
        $.ajax({
            type: "POST",
            url: '/app/logs',
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: "application/json",
            async: false,
            success: function (response) {
                console.log(response)
                $("div.app-logs-container").html(response.result["app_logs"])
            }
        });
    },
    app_dashboard: function (event) {
        event.preventDefault();
        var repository_id = $(event.currentTarget).attr("repository_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('sh.git_repository', 'open_dashboard', ["", { 'id': repository_id }])
            .then(
                function (_response) {
                    var button_dashboard = [
                        {
                            name: _t("Let's start..."),
                            primary: true,
                            onClick: () => {
                                window.open(
                                    'https://' + String(_response['hostname']),
                                    '_new'
                                );
                            },
                        },
                    ];
                    navigator.clipboard.writeText(_response['token']);
                    dialog.add(_t("Token is now in your clipboard, paste it in follow login form."), { 'title': _t('Cluster Administrator'), sticky: false, 'type': 'success', buttons: button_dashboard });
                    $("html, body").animate({ scrollTop: 0 }, "fast");
                }
            );
    },
    save_command: function (btn) {
        var self = this;
        var branch_id = btn.attr("branch_id");
        var command = $("#commands").val();
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.commands', 'save_command', ["", { '_branch_id': parseInt(branch_id), '_command': command }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('COMMANDS LIST'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var commands = response.commands
                        self.draw_commands(commands);
                    }
                }
            );
    },
    create_ssl: function (btn, type) {

        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var autor_id = btn.attr("autor_id");
        var _domain = $("select#_domain").val();
        var ssl_cert_input = document.querySelector('#ssl_cert').files[0];
        var ssl_cert = null;
        var ssl_cert_key_input = document.querySelector('#ssl_cert_key').files[0];
        var ssl_cert_key = null;
        var _method = "create_ssl_external"
        var dialog = this.bindService("notification");

        if (_domain != null && _domain != String('Select')) {
            if (type == "external") {
                var reader = new FileReader();
                try {
                    reader.readAsDataURL(ssl_cert_input);
                }
                catch (error) {
                    dialog.add(_t("Browse and upload a valid certificate"), { 'title': _t('SSL'), sticky: false });
                    $("html, body").animate({ scrollTop: 0 }, "fast");
                    return
                }

                reader.onload = function () {
                    // certificate
                    ssl_cert = reader.result;
                    // certificate key
                    var reader1 = new FileReader();
                    reader1.readAsDataURL(ssl_cert_key_input);
                    try {
                        reader1.readAsDataURL(ssl_cert_key_input);
                    }
                    catch (error) {
                        dialog.add(_t("Browse and upload a valid certificate key"), { 'title': _t('SSL'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                        return
                    }
                    reader1.onload = function () {
                        ssl_cert_key = reader1.result;
                        this.create_ssl_rpc({ '_repository_id': repository_id, '_branch_id': branch_id, '_autor_id': autor_id, '_domain': _domain, 'ssl_cert': ssl_cert, 'ssl_cert_key': ssl_cert_key, "type": type }, _method);
                    };
                    reader1.onerror = function (error) {
                        dialog.add(_t("Browse and upload a valid certificate key"), { 'title': _t('SSL'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    };
                };
                reader.onerror = function (error) {
                    dialog.add(_t("Browse and upload a valid certificate; "), { 'title': _t('SSL'), sticky: false });
                    $("html, body").animate({ scrollTop: 0 }, "fast");
                };
            }
            else {
                var _method = "create_ssl_internal";
                this.create_ssl_rpc({ '_repository_id': repository_id, '_branch_id': branch_id, '_autor_id': autor_id, '_domain': _domain, 'ssl_cert': ssl_cert, 'ssl_cert_key': ssl_cert_key, "type": type }, _method);
            }
        }
        else {
            dialog.add(_t("Select a domain name to create SSL Certificate"), { 'title': _t('SSL'), sticky: false });
            $("html, body").animate({ scrollTop: 0 }, "fast");
        }
    },
    create_ssl_rpc: function (args, _method) {
        var self = this;
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");
        orm.call('kuber.domains_ssl', _method, ["", args])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('SELF SIGNED SSL'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        dialog.add(response.message, { 'title': _t('SELF SIGNED SSL'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                        self.draw_domains_ssl(response.ssl_domains)
                    }
                }
            );
    },
    create_git_repository_branch_from: function () {

        var branch_from = $("#from-branches").val();
        var branch_from_label = $("#from-branches option:selected").text().trim();
        var repository_id = $("#from-branches").attr("repository_id");
        var branch_to = $("#new-referenced-branch").val();
        var dialog = this.bindService("notification");

        try {
            if (branch_to == "") {
                dialog.add(_t("Branch name is required."), { 'title': _t('NEW BRANCH'), sticky: false });
                $("html, body").animate({ scrollTop: 0 }, "fast");
                $("#new-referenced-branch").focus();
            }

            var orm = this.bindService("orm");
            orm.call('sh.git_branch', 'create_git_repository_branch_from', ["", { '_branch_from': branch_from, '_repository_id': repository_id, '_branch_to': branch_to, '_branch_from_label': branch_from_label }])
                .then(
                    function (response) {
                        dialog.add(response.message, { 'title': _t('NEW BRANCH'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                        setInterval(function () { location.reload(); }, 9000);
                    }
                )
        }
        catch (e) {
            setInterval(function () { location.reload(); }, 99000);
        }
    },
    assign_domain: function (btn) {
        var self = this;
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var domain_name = $("#domain_name").val();
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");

        if (domain_name != null) {

            orm.call('kuber.domains', 'verify_domain', ["", { 'domain': domain_name }])
                .then(
                    function (_response) {
                        if (_response == true) {
                            orm.call('sh.git_branch', 'assign_domain', ["", { '_repository_id': repository_id, '_branch_id': branch_id, '_domain_name': domain_name }])
                                .then(
                                    function (response) {
                                        if (response.error == true) {
                                            dialog.add(response.message, { 'title': _t('ASSIGN DOMAIN'), sticky: false });
                                            $("html, body").animate({ scrollTop: 0 }, "fast");
                                        }
                                        else {
                                            var domains = response.domains
                                            self.draw_domains(domains);
                                        }
                                    }
                                );
                        }
                        else {
                            dialog.add(_response, { 'title': _t('ASSIGN DOMAIN'), sticky: false, type: 'success' });
                            $("html, body").animate({ scrollTop: 0 }, "fast");
                        }
                    }
                );
        }
        else {
            dialog.add(_t("Type a domain name."), { 'title': _t('DOMAINS'), sticky: false, type: 'success' });
            $("html, body").animate({ scrollTop: 0 }, "fast");
        }

    },
    restart_branch: function (btn) {
        $('#restart-branch i').addClass('rotate');
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var autor_id = btn.attr("autor_id");
        var _service = $("#_service").val();
        var _database = $("#_database").val();
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");

        orm.call('sh.git_branch', 'restart_branch', ["", { '_repository_id': repository_id, '_branch_id': branch_id, '_autor_id': autor_id, "_service": _service, "_database": _database }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('RESTART SERVICE'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        dialog.add(response.message, { 'title': _t('RESTART SERVICE'), sticky: false, type: 'success' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    $('#restart-branch i').removeClass('rotate');
                }
            );
    },
    autor_and_collaborators_control: function (event) {
        var repository_id = $('.row-active').attr("repository_id");
        var autor_id = $('.row-active').attr("autor_id");
        var dialog = this.bindService("notification");

        var orm = this.bindService("orm");
        orm.call('sh.git_repository', 'autor_and_collaborators_control', ["", { '_repository_id': repository_id, '_autor_id': autor_id }])
            .then(
                function (response) {
                    if (response.error == true)
                    {
                        dialog.add(response.message, { 'title': _t('COLLABORATOR & AUTOR QWEB CONTROL'), sticky: false });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        if (String(response._type) == String("collaborator")) {
                            $('.access-right').remove();
                        }
                        else if (String(response._type) == String("autor")) {
                            $('.access-right').removeClass("access-right");
                        }
                        else {
                            $('.access-right').remove();
                        }
                    }
                }
            );
    },
    get_git_project_branch_commits: function (btn) {
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var autor_id = btn.attr("autor_id");
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");
        orm.call('sh.git_branch', 'get_branch_commits', ["", { '_repository_id': repository_id, '_branch_id': branch_id, '_autor_id': autor_id }])
            .then(
                function (response) {
                    if (response.error == true) {

                        dialog.add(response.message, { 'title': _t('BRANCH COMMITS'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var commits = response.commits
                        if (commits.length) {
                            var commits_html = String("")

                            commits.forEach(commit => {
                                var commit_html = ' \n' +
                                    ' <div class="row"> \n' +
                                    '         <div class="sh-branch-commit"> \n' +
                                    '             <div class="row sh-c-name"> \n' +
                                    '                 <span>' + String(commit['sha']) + '</span> \n' +
                                    '             </div> \n' +
                                    '             <div class="row sh-c-message"> \n' +
                                    '                 <span>' + String(commit['message']) + '</span> \n' +
                                    '             </div> \n' +
                                    '             <div class="row sh-c-author"> \n' +
                                    '                 <span>By </span>  <span class="commited-by">  ' + String(commit['author']) + '</span> \n' +
                                    '             </div> \n' +
                                    '             <div class="row sh-c-link"> \n' +
                                    '                <a href="' + String(commit['url']) + '" class="btn btn-success"> <i class="fa fa-github"></i> <span> Go!</span> </a> \n' +
                                    '             </div> \n' +
                                    '         </div> \n' +
                                    ' </div> \n';

                                commits_html = String(commits_html) + String(commit_html);

                            });
                            $("#sh-history-tab").html(commits_html)
                        }
                    }
                }
            );
    },
    get_code_editor: function (btn) {
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");
        orm.call('sh.git_repository', 'get_code_editor', ["", { '_repository_id': repository_id, '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('CODE EDITOR'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        //$("#sh-shell-tab").html(response.editor)
                        $("a.sh-shell-tab").attr('external_editor', response.editor_external_url);
                    }
                }
            );
    },
    get_pgadmin: function (btn) {
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");
        orm.call('sh.git_repository', 'get_pgadmin', ["", { '_repository_id': repository_id, '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        console.log(response.message);
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                        $("a#pgadmin").remove()
                    }
                    else {
                        $("a#pgadmin").attr('href', response.pgadmin_external_url);
                        $("a#pgadmin").fadeIn()
                    }
                }
            );
    },
    get_branch_connect: function (btn) {
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('sh.git_branch', 'get_branch_connect', ["", { '_repository_id': repository_id, '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('APP CONECTION'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        $("a#app-gateway").attr('href', response.url).fadeIn();
                    }
                }
            );
    },
    get_branches: function (btn) {
        var self = this;
        var repository_id = btn.attr("repository_id");
        var orm = this.bindService("orm");
        orm.call('sh.git_repository', 'get_repository_branches', ["", repository_id,])
            .then(
                function (branches) {
                    var options = "<option>Select</option>";
                    for (var index=0; index < branches.length; index++) {                   
                            options += "<option value='" + String(branches[index]['id']) + "'>" + String(branches[index]['name']) + "</option>";                        
                    }
                    if (branches.length > 0) {
                        $("select#github_branches").html(options);
                    }                    
                }
            );
    },
    get_collaborators: function (btn) {
        var self = this;
        var branch_id = btn.attr("branch_id");
        var dialog = this.bindService("notification");
        var orm = this.bindService("orm");
        orm.call('sh.git_branch', 'get_collaborators', ["", { '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('COLLABORATORS LIST'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var collaborators = response.collaborators
                        self.draw_collaborators(collaborators);
                    }
                }
            );
    },
    draw_collaborators: function (collaborators) {
        var self = this;
        var options = "<option>Select</option>";
        for (var id in collaborators) {
            if (collaborators.hasOwnProperty(id)) {
                var autor_parts = String(collaborators[id]).split(',');
                var row = "<div class='row collaborator-item' autor_id='" + String(autor_parts[0]) + "'><span ><a href='//github.com/codesystemsco' target='_blank'><i autor_id='" + String(autor_parts[0]) + "' class='btn btn-secondary fa fa-trash unssign_collaborator'></i>&nbsp;&nbsp;</span>&nbsp;-&nbsp;<span >" + String(autor_parts[1]) + " </a></span></div>"
                options += "<option value='" + String(autor_parts[0]) + "'>" + String(autor_parts[1]) + "</option>";
            }
        }
        if (collaborators.length > 0) {
            $("select#collaborators_list").html(options);
        }
        else {
            var empty = ' <div class="row-spinner"><i class="fa fa-spinner"></i> No records</div>';
            $(".collaborators_list").html(empty);
        }
    },
    unssign_collaborator: function (btn) {
        var self = this;
        var branch_id = $('.row-active').attr("branch_id");
        var autor_id = $("select#collaborators_list").val();
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('sh.git_branch', 'unssign_collaborator', ["", { '_branch_id': branch_id, '_autor_id': autor_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('UNSSIGN COLLABORATOR'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var collaborators = response.collaborators;
                        self.draw_collaborators(collaborators);
                    }
                }
            );
    },
    web_execute_command: function () {
        var branch_id = $('.row-active').attr("branch_id");
        var command = $("#commands").val();
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.commands', 'web_execute_command', ["", { '_branch_id': branch_id, '_command': command }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('EXECUTE COMMAND'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else { }
                }
            );
    },
    delete_command: function (btn) {
        var self = this;
        var branch_id = $('.row-active').attr("branch_id");
        var command_id = btn.attr("command_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.commands', 'delete_command', ["", { '_branch_id': branch_id, '_command_id': command_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('DELETE COMMAND'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var commands = response.commands;
                        self.draw_commands(commands);
                    }
                }
            );
    },
    delete_domain: function (btn) {
        var self = this;
        var branch_id = $('.row-active').attr("branch_id");
        console.log(btn.val())
        var domain_id = $("#domains_list").val();
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.domains', 'delete_domain', ["", { '_branch_id': branch_id, '_domain_id': domain_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('DELETE DOMAIN'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var domains = response.domains;
                        self.draw_domains(domains);
                    }
                }
            );
    },
    draw_commands: function (commands) {
        var self = this;
        var commands_html = "";
        for (var id in commands) {
            if (commands.hasOwnProperty(id)) {
                var command_id = id;
                var autor_parts = String(commands[id]).split(',');
                var row = "<div class='row command-item' command_id='" + String(autor_parts[0]) + "'><div class='float-left'><i command_id='" + String(autor_parts[0]) + "' class='btn btn-secondary fa fa-trash delete_command'></i>&nbsp;&nbsp;</div><div class='float-left cmd'>" + String(autor_parts[1]) + " </a></div></div>"
                commands_html = String(commands_html) + String(row)
            }
        }
        if (commands.length > 0) {
            $(".commands_list").html(commands_html);
            $(".delete_command").on("click", function (event) {
                event.preventDefault();
                self.delete_command($(this))
            });
        }
        else {
            var empty = ' <div class="row-spinner"><i class="fa fa-spinner"></i> No records</div>';
            $(".commands_list").html(empty);
        }
    },
    get_commands: function (btn) {
        var self = this;
        var branch_id = btn.attr("branch_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.commands', 'get_commands', ["", { '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('COMMANDS LIST'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var commands = response.commands
                        self.draw_commands(commands);
                    }
                }
            );
    },
    assign_collaborator: function (btn) {
        var self = this;
        var repository_id = btn.attr("repository_id");
        var branch_id = btn.attr("branch_id");
        var autor_id = btn.attr("autor_id");
        var autor_name = $("#collaborator_username").val();
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('sh.git_branch', 'assign_collaborator', ["", { '_repository_id': repository_id, '_branch_id': branch_id, '_autor_id': autor_id, '_autor_name': autor_name }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('ASSIGN COLLABORATOR'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var collaborators = response.collaborators
                        self.draw_collaborators(collaborators);
                        dialog.add(_t("Collaborator was assigned to this branch"), { 'title': _t('ASSIGN COLLABORATOR'), sticky: false, type: 'success' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                }
            );
    },
    get_domains: function (btn) {
        var self = this;
        var branch_id = btn.attr("branch_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('sh.git_branch', 'get_domains', ["", { '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('DOMAINS LIST'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var domains = response.domains;
                        self.draw_domains(domains);
                    }
                }
            );
    },
    draw_domains: function (domains) {
        var self = this;
        var options = "<option>Select</option>";
        var domains_options_html = ""
        for (var id in domains) {
            if (domains.hasOwnProperty(id)) {
                var autor_parts = String(domains[id]).split(',');
                var row = "<div class='row domain-item' domain_id='" + String(autor_parts[0]) + "'><span ><i domain_id='" + String(autor_parts[0]) + "' class='btn btn-secondary fa fa-trash delete_domain'></i>&nbsp;&nbsp;</span>&nbsp;-&nbsp;<span >" + String(autor_parts[1]) + " </a></span></div>";
                var row_ssl = "<option value='" + String(autor_parts[0]) + "'>" + String(autor_parts[1]) + "</option>";
                options += "<option value='" + String(autor_parts[0]) + "'>" + String(autor_parts[1]) + "</option>";
                domains_options_html = String(domains_options_html) + String(row_ssl);
            }
        }
        if (domains.length > 0) {
            $("select#domains_list").html(options);
            $("select#_domain").html(domains_options_html);
        }
        else {
            var empty = ' <div class="row-spinner"><i class="fa fa-spinner"></i> No records</div>';
            $(".domains_list").html(empty);
        }
    },
    draw_domains_ssl: function (domains) {
        var domains_html = ""
        var options = "<option>Select</option>";
        for (var id in domains) {
            if (domains.hasOwnProperty(id)) {
                var autor_parts = String(domains[id]).split(',');
                var row = "<div class='row domain-item' domain_id='" + String(autor_parts[0]) + "'><span ><i domain_id='" + String(autor_parts[0]) + "' class='btn btn-secondary fa fa-trash delete_domain_ssl'></i>&nbsp;&nbsp;</span>&nbsp;-&nbsp;<span >" + String(autor_parts[1]) + " </a></span></div>";
                options += "<option value='" + String(autor_parts[0]) + "'>" + String(autor_parts[1]) + "</option>";
            }
        }
        if (domains.length > 0) {
            $("select.ssl_domains_list").html(options);
        }
        else {
            var options = "<option>Select</option>";
            $("select.ssl_domains_list").html(options);
        }
    },
    get_domains_ssl: function (btn) {
        var self = this;
        var branch_id = btn.attr("branch_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.domains_ssl', 'qweb_get_domains_ssl', ["", { '_branch_id': branch_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('SSL DOMAINS LIST'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var domains = response.domains;
                        self.draw_domains_ssl(domains);
                    }
                }
            );
    },
    delete_domain_ssl: function (btn) {
        var self = this;
        var branch_id = $('.row-active').attr("branch_id");
        var domain_ssl_id = btn.attr("domain_id");
        var orm = this.bindService("orm");
        var dialog = this.bindService("notification");
        orm.call('kuber.domains_ssl', 'delete_domain_ssl', ["", { '_branch_id': branch_id, '_domain_ssl_id': domain_ssl_id }])
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('DELETE SSL DOMAIN'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        dialog.add(response.message, { 'title': _t('DELETE SSL DOMAIN'), sticky: false, type: 'success' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                        var domains = response.domains;
                        self.draw_domains_ssl(domains.domains);
                    }
                }
            );
    },
    get_deployments_all: function () {
        var orm = this.bindService("orm");
        var so_server = String($("div#sh_so_server").text()).trim();
        var dialog = this.bindService("notification");
        orm.call('kuber.deploy', 'get_deployments', ["", { '_so_server': so_server }]
        )
            .then(
                function (response) {
                    if (response.error == true) {
                        dialog.add(response.message, { 'title': _t('Deployments List'), sticky: false, type: 'error' });
                        $("html, body").animate({ scrollTop: 0 }, "fast");
                    }
                    else {
                        var deployments = response.deployments
                        if (deployments.length > 0) {
                            var options_html = String('');
                            deployments.forEach(deploy => {
                                var option_html = ' \n' +
                                    ' <option value="' + String(deploy['id']) + '" so_server="' + String(deploy['so_server']) + '"> \n' +
                                    String(deploy['name']) +
                                    ' </div> \n';

                                options_html = String(options_html) + String(option_html);
                            });
                            $("select#deployments_options").html(options_html);
                            var so_server = $('option:selected', $("select#deployments_options")).attr('so_server');
                            $(".deploy_so_server").html(so_server);
                        }
                    }
                }
            );
    },
    hide_new_repository_form: function () {
        $("#sh-cancel-repository").hide();
        $(".sh-form-new-repository").slideUp("fast");
        $(".sh-form-new-repository").fadeOut("slow");
        $("#sh-new-repository").fadeIn("slow");
    }
})